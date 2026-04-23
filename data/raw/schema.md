## Dataset Overview

The data is organized into four logical layers:

- **Master**: reference entities
- **Transaction**: order-level and item-level business events
- **Analytical**: aggregated revenue series for forecasting
- **Operational**: inventory and website operations data

Official released files:

1. `products.csv`
2. `customers.csv`
3. `promotions.csv`
4. `geography.csv`
5. `orders.csv`
6. `order_items.csv`
7. `payments.csv`
8. `shipments.csv`
9. `returns.csv`
10. `reviews.csv`
11. `sales.csv`
12. `sample_submission.csv`
13. `inventory.csv`
14. `web_traffic.csv` 

---

## 1. Master Tables

### 1.1 `products.csv`
Product catalog.

| Column | Type | Description |
|---|---|---|
| `product_id` | int | Primary key |
| `product_name` | str | Product name |
| `category` | str | Product category |
| `segment` | str | Product market segment |
| `size` | str | Product size |
| `color` | str | Product color label |
| `price` | float | Retail price |
| `cogs` | float | Cost of goods sold |

**Constraint**
- `cogs < price` for every product. 

### 1.2 `customers.csv`
Customer master data.

| Column | Type | Description |
|---|---|---|
| `customer_id` | int | Primary key |
| `zip` | int | Postal code, FK → `geography.zip` |
| `city` | str | Customer city |
| `signup_date` | date | Account signup date |
| `gender` | str | Customer gender, nullable |
| `age_group` | str | Customer age group, nullable |
| `acquisition_channel` | str | Marketing channel used at signup, nullable |

Source definition from the requirement PDF. 

### 1.3 `promotions.csv`
Promotion campaign master data.

| Column | Type | Description |
|---|---|---|
| `promo_id` | str | Primary key |
| `promo_name` | str | Campaign name with year |
| `promo_type` | str | Discount type: percentage or fixed amount |
| `discount_value` | float | Discount value based on `promo_type` |
| `start_date` | date | Campaign start date |
| `end_date` | date | Campaign end date |
| `applicable_category` | str | Applicable product category, null if all categories |
| `promo_channel` | str | Distribution channel for promotion, nullable |
| `stackable_flag` | int | Whether multiple promotions can stack |
| `min_order_value` | float | Minimum order value required, nullable |

**Discount formulas**
- If `promo_type = percentage`: `discount_amount = quantity × unit_price × (discount_value / 100)`
- If `promo_type = fixed`: `discount_amount = quantity × discount_value` 

### 1.4 `geography.csv`
Geographic lookup data.

| Column | Type | Description |
|---|---|---|
| `zip` | int | Primary key, postal code |
| `city` | str | City name |
| `region` | str | Geographic region |
| `district` | str | District name |

Source definition from the requirement PDF. 

---

## 2. Transaction Tables

### 2.1 `orders.csv`
Order header data.

| Column | Type | Description |
|---|---|---|
| `order_id` | int | Primary key |
| `order_date` | date | Order date |
| `customer_id` | int | FK → `customers.customer_id` |
| `zip` | int | Shipping postal code, FK → `geography.zip` |
| `order_status` | str | Order processing status |
| `payment_method` | str | Payment method used |
| `device_type` | str | Device used when placing order |
| `order_source` | str | Marketing source that led to the order |

Source definition from the requirement PDF. 

### 2.2 `order_items.csv`
Order line items.

| Column | Type | Description |
|---|---|---|
| `order_id` | int | FK → `orders.order_id` |
| `product_id` | int | FK → `products.product_id` |
| `quantity` | int | Quantity purchased |
| `unit_price` | float | Unit selling price |
| `discount_amount` | float | Total discount applied to this line |
| `promo_id` | str | FK → `promotions.promo_id`, nullable |
| `promo_id_2` | str | FK → `promotions.promo_id`, second promotion, nullable |

Source definition from the requirement PDF. 

### 2.3 `payments.csv`
Order payment data.

| Column | Type | Description |
|---|---|---|
| `order_id` | int | FK → `orders.order_id`, 1:1 relationship |
| `payment_method` | str | Payment method |
| `payment_value` | float | Total payment value for the order |
| `installments` | int | Number of installment periods |

Source definition from the requirement PDF. 

### 2.4 `shipments.csv`
Shipment data.

| Column | Type | Description |
|---|---|---|
| `order_id` | int | FK → `orders.order_id` |
| `ship_date` | date | Shipping date |
| `delivery_date` | date | Delivery date |
| `shipping_fee` | float | Shipping fee, `0` if free shipping |

**Availability rule**
- Exists only for orders with status `shipped`, `delivered`, or `returned`. 

### 2.5 `returns.csv`
Returned product records.

| Column | Type | Description |
|---|---|---|
| `return_id` | str | Primary key |
| `order_id` | int | FK → `orders.order_id` |
| `product_id` | int | FK → `products.product_id` |
| `return_date` | date | Date customer sent return |
| `return_reason` | str | Reason for return |
| `return_quantity` | int | Quantity returned |
| `refund_amount` | float | Refunded amount |

Source definition from the requirement PDF. 

### 2.6 `reviews.csv`
Post-delivery product reviews.

| Column | Type | Description |
|---|---|---|
| `review_id` | str | Primary key |
| `order_id` | int | FK → `orders.order_id` |
| `product_id` | int | FK → `products.product_id` |
| `customer_id` | int | FK → `customers.customer_id` |
| `review_date` | date | Review submission date |
| `rating` | int | Rating from 1 to 5 |
| `review_title` | str | Customer review title |

Source definition from the requirement PDF. 

---

## 3. Analytical Tables

### 3.1 `sales.csv`
Daily revenue data for forecasting model training.

| Column | Type | Description |
|---|---|---|
| `Date` | date | Order date |
| `Revenue` | float | Total net revenue |
| `COGS` | float | Total cost of goods sold |

**Forecasting split defined in the requirement**
- Train: `sales.csv`, from **2012-07-04** to **2022-12-31**
- Test: `sales_test.csv`, from **2023-01-01** to **2024-07-01**

**Note**
- The test set is not publicly released and is used for evaluation on Kaggle.
- Its structure matches `sample_submission.csv`. 

### 3.2 `sample_submission.csv`
Submission format template for the forecasting task.

Required columns:

| Column | Type | Description |
|---|---|---|
| `Date` | date | Forecast date |
| `Revenue` | float | Predicted revenue |
| `COGS` | float | Predicted COGS |

Rows must keep the same order as the official sample submission format. 

---

## 4. Operational Tables

### 4.1 `inventory.csv`
Monthly end-of-month inventory snapshot by product.

| Column | Type | Description |
|---|---|---|
| `snapshot_date` | date | Inventory snapshot date, end of month |
| `product_id` | int | FK → `products.product_id` |
| `stock_on_hand` | int | Ending inventory quantity |
| `units_received` | int | Units received during the month |
| `units_sold` | int | Units sold during the month |
| `stockout_days` | int | Number of out-of-stock days in the month |
| `days_of_supply` | float | Estimated number of days inventory can cover demand |
| `fill_rate` | float | Share of demand fully fulfilled from inventory |
| `stockout_flag` | int | Indicator that a stockout occurred during the month |
| `overstock_flag` | int | Indicator that inventory exceeded needed level |
| `reorder_flag` | int | Indicator that early reorder is needed |
| `sell_through_rate` | float | Share sold out of total available stock |
| `product_name` | str | Product name |
| `category` | str | Product category |
| `segment` | str | Product segment |
| `year` | int | Year extracted from `snapshot_date` |
| `month` | int | Month extracted from `snapshot_date` |

Source definition from the requirement PDF. 

### 4.2 `web_traffic.csv`
Daily website traffic metrics.

| Column | Type | Description |
|---|---|---|
| `date` | date | Traffic date |
| `sessions` | int | Total sessions for the day |
| `unique_visitors` | int | Unique visitors |
| `page_views` | int | Total page views |
| `bounce_rate` | float | Share of sessions with a single-page exit |
| `avg_session_duration_sec` | float | Average session duration in seconds |
| `traffic_source` | str | Traffic acquisition source |

Source definition from the requirement PDF. 

---

## 5. Table Relationships

Official relationship rules stated in the requirement:

| Relationship | Cardinality |
|---|---|
| `orders` <=> `payments` | 1 : 1 |
| `orders` <=> `shipments` | 1 : 0 or 1 (`shipped` / `delivered` / `returned`) |
| `orders` <=> `returns` | 1 : 0 or many (`returned`) |
| `orders` <=> `reviews` | 1 : 0 or many (`delivered`, approximately 20%) |
| `order_items` <=> `promotions` | many : 0 or 1 |
| `products` <=> `inventory` | 1 : many (1 row per product per month) |

Source relationship section from the requirement PDF. 

---

## 6. Notes on Missingness and Nullability

The requirement explicitly marks some columns as nullable:

- `customers.gender`
- `customers.age_group`
- `customers.acquisition_channel`
- `promotions.applicable_category`
- `promotions.promo_channel`
- `promotions.min_order_value`
- `order_items.promo_id`
- `order_items.promo_id_2`

These nullability statements come directly from the published schema descriptions. 

---

## 7. Time Coverage

Published time coverage in the requirement:

- Business simulation period: **2012-07-04** to **2022-12-31**
- Forecast evaluation period: **2023-01-01** to **2024-07-01**

Source dates from the requirement PDF. 
