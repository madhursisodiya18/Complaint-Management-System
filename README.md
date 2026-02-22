# MIT Academy of Engineering - Complaint Management System

A comprehensive web-based complaint management system built with Python Flask, designed specifically for MIT Academy of Engineering students and administrators.

## 🌟 Features

### 🎨 User Interface
- **Light/Dark Mode Toggle**: Seamless theme switching with localStorage persistence
- **Responsive Design**: Mobile-friendly interface using Bootstrap 5
- **College Theme**: Professional design with gradient headers and modern styling
- **Logo-Only Header**: Clean navigation with MIT Academy logo
- **Smooth Transitions**: Animated theme switching and hover effects

### 🔐 Authentication & Security
- **Strict Email Domain Restriction**: Only `@mitaoe.ac.in` emails allowed
- **Gmail Exclusion**: Explicitly blocks `@gmail.com` addresses
- **Role-Based Access**: Separate student and admin interfaces
- **Secure Password Hashing**: Passwords encrypted using Werkzeug
- **Session Management**: Secure user sessions with Flask

### 👥 User Management
- **Student Registration**: Self-registration with email validation
- **Admin Access**: Pre-configured admin account
- **User Profiles**: Personal dashboard and complaint history
- **Real-time Updates**: Live timestamps and status tracking

### 📝 Complaint System
- **Multiple Categories**: Teachers, Students, Staff, and Facilities
- **Status Tracking**: Pending, In Progress, and Resolved states
- **Admin Responses**: Administrators can respond to complaints
- **Complaint History**: Complete audit trail for all complaints
- **Real-time Timestamps**: Accurate creation and resolution times

### 🛠️ Technical Features
- **SQLite Database**: Lightweight, file-based database
- **Flask Framework**: Python web framework for backend
- **Bootstrap 5**: Modern CSS framework for frontend
- **Font Awesome**: Professional icons throughout the interface
- **Google Fonts**: Montserrat and Poppins for typography

## 🚀 Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Installation Steps

1. **Clone or Download the Project**
   ```bash
   cd "Complaint Management System"
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Application**
   ```bash
   python app.py
   ```

4. **Access the Application**
   - Open your browser and go to: `http://localhost:5000`
   - The application will automatically create the database and admin user

## 👤 Default Admin Account

- **Email**: `madhur.sisodiya@mitaoe.ac.in`
- **Password**: `Madhur123@`

## 📱 How to Use

### For Students
1. **Register**: Use your `@mitaoe.ac.in` email address
2. **Login**: Access your personal dashboard
3. **Submit Complaints**: Choose category and provide details
4. **Track Progress**: Monitor complaint status and admin responses
5. **View History**: Access all your submitted complaints

### For Administrators
1. **Login**: Use the admin credentials
2. **View All Complaints**: See complaints from all students
3. **Update Status**: Change complaint status (Pending → In Progress → Resolved)
4. **Respond**: Provide detailed responses to student complaints
5. **Manage System**: Monitor overall system activity

## 🎨 Theme Features

### Light Mode
- Clean white background
- Dark text for readability
- Subtle shadows and borders
- Professional appearance

### Dark Mode
- Dark background for reduced eye strain
- Light text for contrast
- Gradient accents and highlights
- Modern aesthetic

### Theme Toggle
- Located in the navigation bar
- Instant switching between themes
- Remembers user preference
- Smooth transition animations

## 🔒 Security Features

### Email Validation
- **Allowed Domains**: Only `@mitaoe.ac.in`
- **Blocked Domains**: `@gmail.com` and other non-institutional emails
- **Real-time Validation**: Immediate feedback during registration

### Access Control
- **Role-Based Permissions**: Students can only see their own complaints
- **Admin Privileges**: Administrators can view and manage all complaints
- **Session Security**: Automatic logout and session management

## 📊 Database Schema

### Users Table
- `id`: Primary key
- `name`: Full name
- `email`: Email address (unique)
- `password`: Hashed password
- `role`: User role (student/admin)
- `created_at`: Registration timestamp

### Complaints Table
- `id`: Primary key
- `user_id`: Foreign key to users
- `category`: Complaint category
- `subject`: Complaint title
- `description`: Detailed description
- `status`: Current status
- `created_at`: Submission timestamp
- `resolved_at`: Resolution timestamp
- `admin_response`: Admin's response

## 🛠️ Technical Stack

- **Backend**: Python Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Frontend**: HTML5, CSS3, JavaScript
- **CSS Framework**: Bootstrap 5
- **Icons**: Font Awesome 6
- **Fonts**: Google Fonts (Montserrat, Poppins)
- **Security**: Werkzeug password hashing

## 📁 Project Structure

```
Complaint Management System/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
├── instance/
│   └── complaints.db     # SQLite database
├── static/
│   ├── mit_logo.jpg      # MIT Academy logo
│   ├── 1.jpg            # Background image
│   └── logo.png         # Additional logo
└── templates/
    ├── base.html         # Base template with theme toggle
    ├── home.html         # Landing page
    ├── login.html        # Login form
    ├── register.html     # Registration form
    ├── dashboard.html    # User dashboard
    ├── submit_complaint.html  # Complaint submission
    ├── view_complaint.html    # Complaint details
    ├── history.html      # Complaint history
    ├── about.html        # About page
    └── contact.html      # Contact page
```

## 🎯 Key Features Summary

✅ **Light/Dark Mode Toggle** with localStorage persistence  
✅ **Header with Logo Only** (no text)  
✅ **Strict Email Domain Restriction** (@mitaoe.ac.in only)  
✅ **Gmail Domain Exclusion**  
✅ **Responsive Design** with Bootstrap  
✅ **College Theme** with gradient headers  
✅ **Admin and Student Role Management**  
✅ **Complaint Submission and Management**  
✅ **Real-time Timestamps**  
✅ **View History Functionality**  
✅ **Professional UI/UX Design**  

## 🚀 Getting Started

1. Ensure Python 3.7+ is installed
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python app.py`
4. Access at: `http://localhost:5000`
5. Register as a student or login as admin

## 📞 Support

For technical support or questions about the Complaint Management System, please contact the development team.

---

**Built with ❤️ for MIT Academy of Engineering** 