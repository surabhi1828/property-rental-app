# Property Rental Management System (DBMS Mini Project)

This is a full-stack web application for a property rental system, built as a DBMS mini-project. It uses a Python Flask backend to manage a MySQL database and a dynamic HTML/CSS/JavaScript frontend.
The core concept of the project is to connect property owners directly with tenants, eliminating the need for a broker. The system features three distinct user roles, each with a custom dashboard and permissions: Admin, Owner, and Tenant.

---
# Key Features

Public-Facing Homepage: A dynamic, searchable homepage that displays all "Available" properties to the public.

Role-Based Access Control: The system provides three unique roles with separate dashboards and permissions:

# Admin:

View dashboard statistics (total users, total properties).

View and manage all users (Owners and Tenants).

View and manage all properties in the system.

View a "Complaint List" of all reviews submitted by tenants.

View a "Rating Report" that analyzes the average rating of all properties.

# Owner:

View a personalized dashboard with stats (e.g., "Total Properties," "Properties Rented").

Full CRUD: Register new properties, View their own properties, Edit their property details, and Delete their properties.

Manage tenancy: Assign a tenant to an "Available" property (which automatically updates its status).

End a tenancy (which automatically sets the property back to "Available").

View a Monthly Payment Report to track income.

# Tenant:

View a personalized dashboard showing rent status.

View "My Rentals" (both current and past).

Make Payments for their current rental.

Browse all "Available" properties and "Request to Rent".

Submit Reviews (with ratings and comments) for properties they have rented.

---
# Technology Stack

Backend: Python (Flask)

Database: MySQL

Frontend: HTML5, CSS3, and JavaScript (ES6+)

API: RESTful API routes to connect the frontend JavaScript (using fetch) to the Flask backend.


---
# Installation & Setup

Step 1: Clone the repository

Step 2: Install dependencies
    pip install -r requirements.txt

Step 3: Set up the Database

Step 4: Set up Environment Variables

Step 5: Run the application: 
     python app.py
