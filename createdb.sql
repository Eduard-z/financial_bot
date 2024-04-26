create table budget(
    codename varchar(255) primary key,
    daily_limit integer
);

create table category(
    codename varchar(255) primary key,
    name varchar(255),
    is_base_expense boolean,
    aliases text
);

create table expense(
    id integer primary key,
    user_id integer,
    amount integer,
    created datetime,
    category_codename integer,
    raw_text text,
    FOREIGN KEY(category_codename) REFERENCES category(codename)
);

insert into category (codename, name, is_base_expense, aliases)
values
    ("products", "продукты", true, "еда, магазин, магаз"),
    ("beer", "пивко", true, "пиво, пивас, пивасик"),
    ("alcohol", "алкоголь", false, "алко, алкашка"),
    ("coffee", "кофе", true, ""),
    ("cafe", "кафе", true, "ресторан, обед, мак, макдак, kfc, пицца"),
    ("transport", "общ. транспорт", true, "метро, автобус, metro"),
    ("taxi", "такси", false, ""),
    ("internet", "телефон и интернет", false, "инет, inet, velcom, телефон"),
    ("rent", "аренда квартиры", false, "аренда, квартира"),
    ("komunalka", "коммунальные расходы", false, "коммуналка"),
    ("dress", "одежда", false, "одежда, обувь"),
    ("beauty", "красота", false, "косметика, ногти, стрижка, маникюр, педикюр"),
    ("health", "здоровье", true, "аптека, лекарства, мед услуги"),
    ("household", "бытовые расходы", true, "мила, посуда"),
    ("entertainment", "развлечения", false, "кино, театр"),
    ("reserve", "резерв", true, "отложено"),
    ("other", "прочее", true, "");

insert into budget(codename, daily_limit) values ('base', 170);