import mysql.connector
def db_conn():
    # no database selected on purpose: create_database() must be able to run
    # on a fresh server where mystore does not exist yet. all queries in this
    # module therefore use the mystore. prefix explicitly.
    conn = mysql.connector.connect(host="localhost",username="root",password="root")
    return conn


def create_database():
    db = db_conn()
    curr = db.cursor()

    q = "create database if not exists mystore;"
    curr.execute(q)

    curr.close()
    db.close()


def create_inventory_table():
    db = db_conn()
    curr = db.cursor()

    q = """
    create table if not exists mystore.inventory (
item_id int primary key auto_increment,
product_code int(30),
product_name varchar(255),
product_color varchar(255),
product_size enum('s','m','l','xl','xxl'),
product_price int(30),
product_status enum('ava','sold','ref') default 'ava',
status_update datetime default current_timestamp on update current_timestamp
);
    """

    curr.execute(q)
    curr.close()
    db.close()




def create_history_table():
    db = db_conn()
    curr = db.cursor()

    q = """
    create table if not exists mystore.status_history (
    history_id int primary key auto_increment,
    item_id int,
    product_code int,
    product_name varchar(255),
    product_color varchar(255),
    product_size varchar(10),
    old_status enum('ava','sold','ref'),
    new_status enum('ava','sold','ref') not null,
    changed_at datetime default current_timestamp
    );
    """

    curr.execute(q)
    curr.close()
    db.close()


def create_sales_table():
    db = db_conn()
    curr = db.cursor()

    q = """
    create table if not exists mystore.sales (
    sale_id int primary key auto_increment,
    item_id int not null,
    product_code int,
    product_name varchar(255),
    product_color varchar(255),
    product_size varchar(10),
    sale_price decimal(10,2),
    customer_name varchar(255),
    payment_method varchar(50),
    sale_date datetime default current_timestamp
    );
    """

    curr.execute(q)
    curr.close()
    db.close()


def ensure_saled_status():
    # migrate existing tables: add 'saled' to product_status enum if missing
    db = db_conn()
    curr = db.cursor()

    curr.execute("""
    select 1 from information_schema.columns
    where table_schema = 'mystore' and table_name = 'inventory' and column_name = 'product_status';
    """)
    exists = curr.fetchone()

    if exists:
        curr.execute("""
        select column_type from information_schema.columns
        where table_schema = 'mystore' and table_name = 'inventory' and column_name = 'product_status';
        """)
        col_type = curr.fetchone()[0]
        if 'saled' not in col_type:
            curr.execute("""
            alter table mystore.inventory modify product_status enum('ava','sold','ref','saled') default 'ava';
            """)
            db.commit()

    curr.close()
    db.close()


def ensure_saled_in_history():
    # migrate status_history table: add 'sale' to old_status and new_status enums if missing
    db = db_conn()
    curr = db.cursor()

    for col in ['old_status', 'new_status']:
        curr.execute("""
        select column_type from information_schema.columns
        where table_schema = 'mystore' and table_name = 'status_history' and column_name = %s;
        """, (col,))
        row = curr.fetchone()
        if row:
            col_type = row[0]
            # fix if 'saled' exists instead of 'sale', or if 'sale' is missing
            if 'sale' not in col_type:
                try:
                    null_clause = '' if col == 'old_status' else ' not null'
                    curr.execute(f"""
                    alter table mystore.status_history modify {col} enum('ava','sold','ref','sale'){null_clause};
                    """)
                    db.commit()
                except Exception:
                    db.rollback()

    curr.close()
    db.close()


def ensure_column(table_name,column_name,definition):
    # migrate existing tables: add the column only if it is missing
    db = db_conn()
    curr = db.cursor()

    curr.execute("""
    select 1 from information_schema.columns
    where table_schema = 'mystore' and table_name = %s and column_name = %s;
    """,(table_name,column_name))
    exists = curr.fetchone()

    if exists is None:
        curr.execute(f"alter table mystore.{table_name} add column {column_name} {definition};")
        db.commit()

    curr.close()
    db.close()


def record_status_history(curr,item_id,pro_code,pro_name,pro_color,pro_size,old_status,new_status):
    q = """
insert into mystore.status_history (item_id,product_code,product_name,product_color,product_size,old_status,new_status) values (%s,%s,%s,%s,%s,%s,%s)
"""
    curr.execute(q,(item_id,pro_code,pro_name,pro_color,pro_size,old_status,new_status))



def is_product_code_used(pro_code,pro_name,pro_color,pro_size):
    # a code counts as "used" only when it belongs to a product with
    # different attributes; restocking the identical product is allowed
    db = db_conn()
    curr = db.cursor()

    q = """
    select 1
    from mystore.inventory
    where product_code = %s
    and (product_name <> %s or product_color <> %s or product_size <> %s)
    limit 1;
    """
    curr.execute(q,(pro_code,pro_name,pro_color,pro_size))
    used = curr.fetchone() is not None

    curr.close()
    db.close()
    return used


def add_products_to_inventory(pro_code,pro_name,pro_color,pro_size,pro_price):
    db = db_conn()
    curr = db.cursor()
    # status => ava,sold,ref
    q = """
insert into mystore.inventory (product_code,product_name,product_color,product_size,product_price) values (%s,%s,%s,%s,%s)
"""
    curr.execute(q,(pro_code,pro_name,pro_color,pro_size,pro_price))
    item_id = curr.lastrowid
    record_status_history(curr,item_id,pro_code,pro_name,pro_color,pro_size,None,'ava')
    db.commit()
    curr.close()
    db.close()


def mark_item_sold(pro_code):
    db = db_conn()
    curr = db.cursor()

    # prefer an available item; fall back to a refunded one when stock is out
    curr.execute("""
    select item_id,product_name,product_color,product_size,product_status
    from mystore.inventory
    where product_code = %s and product_status in ('ava','ref')
    order by field(product_status,'ava','ref'),item_id
    limit 1;
    """,(pro_code,))
    row = curr.fetchone()
    if row is None:
        curr.close()
        db.close()
        return 0  # nothing available or refunded with that code

    item_id,pro_name,pro_color,pro_size,old_status = row
    curr.execute("""
    update mystore.inventory
    set product_status = 'sold'
    where item_id = %s;
    """,(item_id,))
    record_status_history(curr,item_id,pro_code,pro_name,pro_color,pro_size,old_status,'sold')
    db.commit()

    curr.close()
    db.close()
    return 1  # an item was marked


def mark_item_refunded(pro_code):
    db = db_conn()
    curr = db.cursor()

    # refund only possible on items that were sold (left the inventory)
    curr.execute("""
    select item_id,product_name,product_color,product_size
    from mystore.inventory
    where product_code = %s and product_status = 'sold'
    limit 1;
    """,(pro_code,))
    row = curr.fetchone()
    if row is None:
        curr.close()
        db.close()
        return 0  # no sold item with that code

    item_id,pro_name,pro_color,pro_size = row
    curr.execute("""
    update mystore.inventory
    set product_status = 'ref'
    where item_id = %s;
    """,(item_id,))
    record_status_history(curr,item_id,pro_code,pro_name,pro_color,pro_size,'sold','ref')
    db.commit()

    curr.close()
    db.close()
    return 1  # an item was refunded


def create_sale(pro_code, sale_amount=None, customer_name=None):
    db = db_conn()
    curr = db.cursor()

    # find available item (not sold, refunded, or saled)
    curr.execute("""
    select item_id,product_name,product_color,product_size,product_price
    from mystore.inventory
    where product_code = %s and product_status = 'ava'
    order by item_id limit 1;
    """,(pro_code,))
    row = curr.fetchone()
    if row is None:
        curr.close()
        db.close()
        return 0  # no available item with that code

    item_id,pro_name,pro_color,pro_size,pro_price = row
    final_price = sale_amount if sale_amount is not None else pro_price

    # update inventory to 'saled'
    curr.execute("""
    update mystore.inventory
    set product_status = 'saled'
    where item_id = %s;
    """,(item_id,))

    # record in status_history (use 'sale' instead of 'saled' due to MySQL enum length)
    record_status_history(curr,item_id,pro_code,pro_name,pro_color,pro_size,'ava','sale')

    # insert into sales table (payment_method left as NULL for backward compatibility)
    curr.execute("""
    insert into mystore.sales (item_id,product_code,product_name,product_color,product_size,sale_price,customer_name,payment_method)
    values (%s,%s,%s,%s,%s,%s,%s,NULL)
    """,(item_id,pro_code,pro_name,pro_color,pro_size,final_price,customer_name))

    db.commit()
    curr.close()
    db.close()
    return 1  # a sale was created


def delete_sale(sale_id):
    """Delete a sale and restore the item to available status"""
    db = db_conn()
    curr = db.cursor()

    # get sale details to restore the item
    curr.execute("""
    select item_id,product_code,product_name,product_color,product_size,sale_price
    from mystore.sales
    where sale_id = %s
    """,(sale_id,))
    row = curr.fetchone()
    if row is None:
        curr.close()
        db.close()
        return 0  # sale not found

    item_id,pro_code,pro_name,pro_color,pro_size,sale_price = row

    # restore item to 'ava' status
    curr.execute("""
    update mystore.inventory
    set product_status = 'ava'
    where item_id = %s
    """,(item_id,))

    # record in status_history (use 'sale' instead of 'saled' due to MySQL enum length)
    record_status_history(curr,item_id,pro_code,pro_name,pro_color,pro_size,'sale','ava')

    # delete from sales table
    curr.execute("delete from mystore.sales where sale_id = %s",(sale_id,))

    db.commit()
    curr.close()
    db.close()
    return 1  # sale deleted, item restored


def remove_inventory_item(pro_code):
    db = db_conn()
    curr = db.cursor()

    # remove a single item with that code (any status except saled)
    curr.execute("""
    select item_id,product_name,product_color
    from mystore.inventory
    where product_code = %s and product_status != 'saled'
    order by item_id
    limit 1;
    """,(pro_code,))
    row = curr.fetchone()
    if row is None:
        curr.close()
        db.close()
        return 0  # no item with that code

    item_id,pro_name,pro_color = row
    curr.execute("""
    delete from mystore.inventory
    where item_id = %s;
    """,(item_id,))
    db.commit()

    curr.close()
    db.close()
    return 1  # one item was removed


def remove_inventory_items_by_code(pro_code):
    db = db_conn()
    curr = db.cursor()

    # remove every item sharing that product code (any status except saled)
    q = """
    delete from mystore.inventory
    where product_code = %s and product_status != 'saled';
    """
    curr.execute(q,(pro_code,))
    db.commit()
    removed = curr.rowcount

    curr.close()
    db.close()
    return removed


def get_inventory_stock():
    db = db_conn()
    curr = db.cursor()

    q = """
    select product_code,product_name,product_color,product_size,count(*)
    from mystore.inventory
    where product_status = 'ava'
    group by product_code,product_name,product_color,product_size;
    """
    curr.execute(q)
    stock = curr.fetchall()

    curr.close()
    db.close()
    return stock


def get_refunded_stock():
    db = db_conn()
    curr = db.cursor()

    q = """
    select product_code,product_name,product_color,product_size,count(*)
    from mystore.inventory
    where product_status = 'ref'
    group by product_code,product_name,product_color,product_size;
    """
    curr.execute(q)
    stock = curr.fetchall()

    curr.close()
    db.close()
    return stock


def get_code_assignments():
    db = db_conn()
    curr = db.cursor()

    # one row per product code with the attributes assigned to it
    q = """
    select product_code,product_name,product_color,product_size
    from mystore.inventory
    group by product_code,product_name,product_color,product_size
    order by product_code;
    """
    curr.execute(q)
    rows = curr.fetchall()

    curr.close()
    db.close()
    return rows


def get_status_summary():
    db = db_conn()
    curr = db.cursor()

    q = """
    select product_status,count(*)
    from mystore.inventory
    group by product_status;
    """
    curr.execute(q)
    rows = curr.fetchall()

    curr.close()
    db.close()

    summary = {"ava": 0, "sold": 0, "ref": 0}
    for status,count in rows:
        summary[status] = count
    return summary


def get_available_variants():
    db = db_conn()
    curr = db.cursor()

    # one row per name+color+size combination still in stock
    q = """
    select product_name,product_color,product_size,count(*)
    from mystore.inventory
    where product_status = 'ava'
    group by product_name,product_color,product_size
    order by product_name,product_color,field(product_size,'s','m','l','xl','xxl');
    """
    curr.execute(q)
    rows = curr.fetchall()

    curr.close()
    db.close()
    return rows


def get_refunded_items():
    db = db_conn()
    curr = db.cursor()

    # one row per refunded item, newest refund first
    q = """
    select product_code,product_name,product_color,product_size,product_price,status_update
    from mystore.inventory
    where product_status = 'ref'
    order by status_update desc,item_id desc;
    """
    curr.execute(q)
    rows = curr.fetchall()

    curr.close()
    db.close()
    return rows


def get_sold_variants():
    db = db_conn()
    curr = db.cursor()

    q = """
    select product_name,product_color,product_size,count(*),sum(product_price)
    from mystore.inventory
    where product_status = 'sold'
    group by product_name,product_color,product_size
    order by product_name,product_color,field(product_size,'s','m','l','xl','xxl');
    """
    curr.execute(q)
    rows = curr.fetchall()

    curr.close()
    db.close()
    return rows


def get_refunded_variants():
    db = db_conn()
    curr = db.cursor()

    q = """
    select product_name,product_color,product_size,count(*),sum(product_price)
    from mystore.inventory
    where product_status = 'ref'
    group by product_name,product_color,product_size
    order by product_name,product_color,field(product_size,'s','m','l','xl','xxl');
    """
    curr.execute(q)
    rows = curr.fetchall()

    curr.close()
    db.close()
    return rows


def get_status_history():
    db = db_conn()
    curr = db.cursor()

    q = """
    select changed_at,product_code,product_name,product_color,product_size,old_status,new_status
    from mystore.status_history
    order by changed_at desc,history_id desc;
    """
    curr.execute(q)
    history = curr.fetchall()

    curr.close()
    db.close()
    return history


def get_status_history_filtered(start_date=None, end_date=None):
    db = db_conn()
    curr = db.cursor()

    q = """
    select changed_at,product_code,product_name,product_color,product_size,old_status,new_status
    from mystore.status_history
    where 1=1
    """
    params = []

    if start_date:
        q += " and changed_at >= %s"
        params.append(start_date)
    if end_date:
        q += " and changed_at <= %s"
        params.append(end_date + " 23:59:59")

    q += " order by changed_at desc,history_id desc;"

    curr.execute(q, params)
    history = curr.fetchall()

    curr.close()
    db.close()
    return history


def get_sales():
    db = db_conn()
    curr = db.cursor()

    q = """
    select sale_id,product_code,product_name,product_color,product_size,sale_price,customer_name,payment_method,sale_date
    from mystore.sales
    order by sale_date desc,sale_id desc;
    """
    curr.execute(q)
    sales = curr.fetchall()

    curr.close()
    db.close()
    return sales


def get_sales_summary():
    db = db_conn()
    curr = db.cursor()

    q = """
    select count(*), sum(sale_price)
    from mystore.sales;
    """
    curr.execute(q)
    row = curr.fetchone()

    curr.close()
    db.close()
    return row if row else (0, 0)


def get_sales_by_variant():
    db = db_conn()
    curr = db.cursor()

    q = """
    select product_name,product_color,product_size,count(*),sum(sale_price)
    from mystore.sales
    group by product_name,product_color,product_size
    order by product_name,product_color,field(product_size,'s','m','l','xl','xxl');
    """
    curr.execute(q)
    rows = curr.fetchall()

    curr.close()
    db.close()
    return rows


def clear_status_history():
    db = db_conn()
    curr = db.cursor()

    q = "delete from mystore.status_history;"
    curr.execute(q)
    db.commit()
    removed = curr.rowcount

    curr.close()
    db.close()
    return removed


def reset_inventory():
    db = db_conn()
    curr = db.cursor()

    q = "delete from mystore.inventory;"
    curr.execute(q)
    db.commit()
    removed = curr.rowcount

    curr.close()
    db.close()
    return removed