# College Management System

## Overview

This is a comprehensive College Management System built with Flask that provides functionality for managing students, teachers, courses, departments, attendance, and grades. The system offers a web-based interface for educational institutions to handle their core administrative tasks including student enrollment, faculty management, course scheduling, attendance tracking, and academic performance monitoring.

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Frontend Architecture
- **Template Engine**: Jinja2 templates with Flask
- **UI Framework**: Bootstrap 5 with custom dark theme
- **Styling**: FontAwesome icons for visual elements
- **Responsive Design**: Mobile-first approach with Bootstrap grid system
- **Navigation**: Role-based navigation with authentication-aware menus

### Backend Architecture
- **Web Framework**: Flask with Python
- **Application Structure**: Modular route-based architecture
- **Authentication**: Flask-Login with role-based access control
- **Session Management**: Flask sessions with configurable secret key
- **Password Security**: Werkzeug password hashing
- **Error Handling**: Flash message system for user feedback
- **Logging**: Python logging for debugging and monitoring

### Authentication System
- **User Management**: User model with secure password hashing
- **Role-Based Access**: Three user roles (Admin, Teacher, Student)
- **Access Control**: Route decorators for role-based permissions
- **Session Security**: Flask-Login session management
- **Default Account**: Admin user (username: admin, password: admin123)

### Data Storage Architecture
- **Database**: SQLite with SQLAlchemy ORM
- **Data Layer**: SQLAlchemy models with relationships
- **Data Format**: Relational database with foreign key constraints
- **Tables**: Users, Students, Teachers, Courses, Departments, Attendance, Grades
- **Data Persistence**: Automatic table creation and default admin user setup

### Core Modules
- **Student Management**: CRUD operations for student records with course enrollment
- **Teacher Management**: Faculty information and department assignments
- **Course Management**: Course catalog with instructor assignments and department linkage
- **Department Management**: Organizational structure with department heads
- **Attendance System**: Date-based attendance tracking per course
- **Grade Management**: Academic performance tracking with multiple assessment types

### Route Architecture
- **RESTful Design**: Clear URL patterns for different operations
- **CRUD Operations**: Create, Read, Update, Delete for all entities
- **Form Handling**: POST/GET method distinction for data operations
- **Error Handling**: Graceful failure with user-friendly messages

## External Dependencies

### Core Framework Dependencies
- **Flask**: Web application framework
- **Jinja2**: Template engine (included with Flask)

### Database
- **Replit DB**: Built-in key-value database service
- **JSON**: Data serialization format

### Frontend Libraries
- **Bootstrap 5**: CSS framework with dark theme variant
- **FontAwesome 6**: Icon library for UI elements

### Python Standard Libraries
- **os**: Environment variable management
- **logging**: Application logging
- **json**: Data serialization/deserialization

### Development Environment
- **Replit**: Cloud-based development and hosting platform
- **Python 3**: Runtime environment