# 🛒 Shop Management & E-Commerce System

[![Python](https://img.shields.io/badge/Python-3.14-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-6.1.1-092E20?logo=django&logoColor=white)](https://www.djangoproject.com/)
[![DRF](https://img.shields.io/badge/DRF-3.18.1-red?logo=django&logoColor=white)](https://www.django-rest-framework.org/)
[![Neon Database](https://img.shields.io/badge/Cloud_Database-Neon_PostgreSQL-00E599?logo=postgresql&logoColor=white)](https://neon.tech/)
[![Authentication](https://img.shields.io/badge/Auth-SimpleJWT_%26_Djoser-orange)](https://django-rest-framework-simplejwt.readthedocs.io/)
[![Currency](https://img.shields.io/badge/Currency-৳_BDT-brightgreen)](#)

A scalable, cloud-connected enterprise e-commerce platform and inventory management system built with **Django**, **Django REST Framework (DRF)**, and **Neon Serverless PostgreSQL**.

---

## 👥 Project Team & Contributors

| Role | Name | Student ID | Key Responsibilities & Contributions |
| :--- | :--- | :---: | :--- |
| **Lead Developer & Architect** | **Md Jamshed Alam** | **2023100010017** | **System Architecture, Core Backend & ORM, Neon PostgreSQL Cloud Integration, Business Services, Public Storefront & REST APIs** |
| **Associate Contributor** | **Sk. Ashiqur Rahman Akash** | **2023100010022** | UI Layout Assistance, Template Styling Support, Documentation & Requirements Gathering |
| **Associate Contributor** | **Mirza Safunur Rahman** | **2023100010251** | Feature Testing, Product Data Entry & Catalog Verification, Bug Reporting & QA |

---

## 📌 Project Overview

Traditional retail operations often struggle with manual stock tracking, disconnected storefronts, and synchronization delays between customer purchases and warehouse inventory. 

This **Shop Management System** resolves these challenges through:
1. **Public Customer Storefront (`/`)**: A fast, mobile-responsive catalog where anyone can browse products, search, and view details in **Bangladeshi Taka (`৳`)** without mandatory login.
2. **Dedicated Staff Portal (`/dashboard/` & `/login/`)**: Secured by JSON Web Tokens (JWT) with one-click demo credentials for swift evaluation.
3. **Automated Inventory & Audit Trail**: Real-time stock deductions upon order dispatch and automated restocks upon return processing.
4. **Cloud-Hosted Database**: Connected to **Neon Serverless PostgreSQL (AWS ap-southeast-1)** with connection pooling.

---

## 🛠️ Technology Stack

| Layer | Technology | Details |
| :--- | :--- | :--- |
| **Backend Framework** | Python 3.14 & Django 6.1.1 | High-level web framework for ORM, security, and routing |
| **API Architecture** | Django REST Framework (DRF) 3.18.1 | RESTful API endpoints with filtering and pagination |
| **Cloud Database** | Neon Serverless PostgreSQL (v18.0) | Cloud-hosted relational storage connected via `psycopg 3.3.6` |
| **Authentication** | SimpleJWT & Djoser | Stateless JWT token authentication with HttpOnly cookies & Bearer tokens |
| **Frontend UI** | HTML5, Vanilla CSS & Modern JS | Clean UI utilizing Bootstrap 5.3 and Bootstrap Icons |
| **Configuration** | `python-dotenv` & `dj-database-url` | Secure cloud environment variables & dynamic DB routing |

---

## ✨ Key Features & Capabilities

### 🛍️ 1. Public Storefront (Open Access)
- **Zero-Barrier Browsing**: Shoppers can freely browse the full catalog without needing an account.
- **Hero Promotional Banner**: Catchy introductory banner with store value guarantees (Authentic Items, Fast Delivery, 24/7 Care).
- **Live Instant Search**: Real-time JavaScript search filtering products by title, SKU, or category without page refreshes.
- **Dynamic Category Filter**: Filter buttons dynamically fetched from database collections and product types.
- **Localized Currency (`৳`)**: Native display of Bangladeshi Taka across all product listings, discounts, and modals.
- **Quick View Modal**: Interactive popup showing high-res images, SKU code, stock availability count, and descriptions.

### 🔐 2. Staff Authentication & Portal
- **JWT Protection**: Secure cookie and bearer authorization verified via custom `JWTRequiredMixin`.
- **One-Click Demo Credentials**: Built-in "Quick Fill" button on `/login/` with pre-filled test credentials:
  - **Email:** `admin@gmail.com`
  - **Password:** `admin`
- **Navigation Shortcuts**: Quick links between the public storefront, staff dashboard, and Django Admin.

### 📦 3. Automated Inventory Engine
- **Atomic Stock Deductions**: Stock is automatically reduced when an order is flagged as `dispatched`.
- **Automated Restocking**: Customer returns automatically replenish available inventory.
- **Immutable Transaction Logs**: Every inventory movement creates an `InventoryTransaction` record documenting the user, timestamp, quantity, and reason.

### 📋 4. Order State Machine
- Enforced order progression: `Pending` &rarr; `Confirmed` &rarr; `Processing` &rarr; `Dispatched` &rarr; `Delivered`.
- Financial breakdown calculating subtotal, discount deductions, shipping costs, and final totals.
- Complete audit trail in `OrderStatusLog` recording who changed what and when.

---

## 🗄️ Database Architecture & Data Models

- **`User` (`auth_app`)**: Custom user model using email as unique login identifier, with staff and role attributes.
- **`ProductType` (`store`)**: Classification hierarchy (e.g., *General, Clothing, Electronics, Footwear*).
- **`Collection` (`store`)**: Marketing groups (e.g., *New Arrivals, Featured, Summer Collection*).
- **`Product` (`store`)**: Core catalog entity with title, slug, SKU, main/new/old pricing, stock count, and images.
- **`ProductChoice` & `ProductChoiceValue` (`store`)**: Dynamic variants (*Size: S, M, L, XL; Color: Black, White, Red*).
- **`ProductVariant` (`store`)**: Sellable SKU variants with independent pricing overrides and stock counts.
- **`Order` & `OrderItem` (`store`)**: Order headers and line-item details with tracking numbers and customer info.
- **`InventoryTransaction` (`store`)**: Comprehensive stock tracking log.
- **`OrderStatusLog` (`store`)**: Audit trail for order state changes.

---

## 🚀 Setup & Execution Guide

### 1. Clone & Open Project Directory
```bash
git clone https://github.com/Jamshed-Dev/shop-management.git
cd shop-management
```

### 2. Activate Virtual Environment
```powershell
# Windows PowerShell:
.\venv\Scripts\Activate.ps1

# Windows Command Prompt:
.\venv\Scripts\activate.bat
```

### 3. Configure Cloud Database (`.env`)
Ensure your `.env` file contains your Neon PostgreSQL connection string:
```env
DATABASE_URL=postgresql://neondb_owner:npg_YHem4KzUfE6g@ep-young-moon-b3c0j242-pooler.c-4.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

### 4. Run Migrations & Start Server
```powershell
# Apply database migrations
python manage.py migrate

# Launch the development server
python manage.py runserver
```

---

## 🌐 URLs & Access Endpoints

| Resource | URL | Access / Credentials |
| :--- | :--- | :--- |
| **Public Storefront** | [http://127.0.0.1:8000/](http://127.0.0.1:8000/) | **Open to All** (No login required) |
| **Staff Login Portal** | [http://127.0.0.1:8000/login/](http://127.0.0.1:8000/login/) | `admin@gmail.com` / `admin` (Click **Quick Fill**) |
| **Staff Dashboard** | [http://127.0.0.1:8000/dashboard/](http://127.0.0.1:8000/dashboard/) | Requires Staff / Superuser Login |
| **Django Admin Panel** | [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/) | `admin@gmail.com` or `jamshed@gmail.com` |
| **REST API Base** | [http://127.0.0.1:8000/api/](http://127.0.0.1:8000/api/) | DRF Browsable API Endpoints |

---

## 📄 Project Documentation PDF

A formal submission-ready **Project Report PDF** is included in the root directory:
- 📑 **[`Shop_Management_System_Project_Report.pdf`](./Shop_Management_System_Project_Report.pdf)**

---

## 🔮 Future Enhancements
- [ ] Integration with Bangladeshi payment gateways (**bKash, Nagad, SSLCommerz**).
- [ ] Automated SMS & Email notifications on order dispatch.
- [ ] Mobile app client powered by the existing DRF REST APIs.
- [ ] Advanced sales analytics and profit margin dashboard.

---

### 📜 License
Developed for academic presentation and store management purposes. All rights reserved &copy; 2026.
