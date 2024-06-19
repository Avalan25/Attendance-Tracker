from flask import Flask, make_response, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, JWTManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from flask_mail import Mail, Message
import psycopg2
from datetime import datetime, timedelta
from flasgger import Swagger, swag_from
import yaml



app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:avalan@localhost:5432/swagger'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'admin'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USERNAME'] = 'spicyboy153@gmail.com'
app.config['MAIL_PASSWORD'] = 'Spicyboy153'
app.config['MAIL_DEBUG'] = True
app.config['SECRET_KEY'] = '521ca85a63664803b13d7300f6beae18'
# app.config['SWAGGER'] = {
#     'title': 'Attendance Tracker',
#     'uiversion': 3
# }
db = SQLAlchemy(app)
jwt = JWTManager(app)
mail = Mail(app)
swagger = Swagger(app, template_file=r'C:\Users\91902\Desktop\Vs code\AttendaceTracker\Attendance\New Attendance\swagger_doc\swagger.yaml')


# creating admin table in attendance database
class Admin(db.Model):
    Admin_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)


with app.app_context():
    db.create_all()


# user table
class User(db.Model):
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    Admin_id = db.Column(db.Integer, db.ForeignKey('admin.Admin_id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


with app.app_context():
    db.create_all()


# attendance table
class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    login_time = db.Column(db.DateTime)
    logout_time = db.Column(db.DateTime)
    status = db.Column(db.String(10), nullable=False)


with app.app_context():
    db.create_all()


# leaves table
class Leaves(db.Model):
    LeaveId = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)
    username = db.Column(db.String(50), nullable=False)
    from_date = db.Column(db.String(50), nullable=False)
    to_date = db.Column(db.String(50), nullable=False)
    reason = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(50), nullable=False)


with app.app_context():
    db.create_all()


def send_verification_email(user):
    try:
        msg = Message('Welcome to Autointelli!', sender='mohamedazeems069@gmail.com', recipients=[user.email])
        msg.body = f"Hello {user.username},\n\nYour account has been created successfully.\n\nUsername: {user.username}\nUseremail: {user.email}\nPassword: {user.password}\n\nThank you!"
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)


def send_leave_email(leaves, user):
    try:
        msg = Message('Leave Application', sender='shanmugasundar.robotics@gmail.com',
                      recipients=['sundaradnim@gmail.com', user.email])
        msg.body = f"Hello request for leave is submitted successfully ,\n\nYour leave details\n\nfrom_date: {leaves.from_date}\nto_date: {leaves.to_date}\nreason: {leaves.reason}\nstatus: {leaves.status}\n\nThank you!\n{leaves.username}"
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)


def send_leave_approval_email(leaves, user):
    try:
        msg = Message('Leave Application Approval', sender='shanmugasundar.robotics@gmail.com', recipients=[user.email])
        msg.body = f"Hello request for leave is Approved successfully ,\n\nYour Leave details.\n\nLeaveId: {leaves.LeaveId}\nuser_id: {leaves.user_id}\nusername: {leaves.username}\nfrom_date: {leaves.from_date}\nto_date: {leaves.to_date}\nreason: {leaves.reason}\nstatus: {leaves.status}\n\nThank you!\n{leaves.username}"
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)


def send_leave_rejection_email(leaves, user):
    try:
        msg = Message('Leave Application Rejection', sender='shanmugasundar.robotics@gmail.com',
                      recipients=[user.email])
        msg.body = f"Hello request for leave is Rejected. ,\n\nYour Leave details.\n\nLeaveId: {leaves.LeaveId}\nuser_id: {leaves.user_id}\nusername: {leaves.username}\nfrom_date: {leaves.from_date}\nto_date: {leaves.to_date}\nreason: {leaves.reason}\nstatus: {leaves.status}\n\nThank you!\n{leaves.username}"
        mail.send(msg)
        print("Email sent successfully!")
    except Exception as e:
        print("Error sending email:", e)



# admin login
@app.route('/login', methods=['POST'])
@swag_from('swagger_doc/swagger.yaml')
def login():

    data = request.get_json()
    try:
        Email = data.get('Email')
        password = data.get('password')
        if not Email or not password:
            return jsonify({'message': 'Email and password are required'}), 400

        admin = Admin.query.filter_by(Email=Email, password=password).first()
        if not admin:
            return jsonify({'message': 'Invalid credentials'}), 401

        # If credentials are valid, create and return JWT token
        access_token = create_access_token(identity=admin.Email)
        return jsonify({"message": "Logged in successfully", "access_token": access_token}), 200
    except Exception as e:
        return jsonify({"message": "Error logging in"}), 500


#  user login and attendance login
@app.route('/userlogin', methods=['POST'])
@swag_from('swagger_doc/swagger.yaml')
def userlogin():
    data = request.get_json()
    try:
        email = data.get('email')
        password = data.get('password')


        user = User.query.filter_by(email=email, password=password).first()
        if user and user.email == email:

            status = 'absent'
            last_attendance = Attendance.query.filter_by(user_id=user.user_id).order_by(Attendance.id.desc()).first()
            if last_attendance and last_attendance.logout_time:
                status = 'present'


            new_attendance = Attendance(
                user_id=user.user_id,
                username=user.username,
                login_time=datetime.now().replace(microsecond=0),
                status=status
            )
            db.session.add(new_attendance)
            db.session.commit()

            access_token = create_access_token(identity=user.user_id)
            return jsonify({"message": "Attendance logged in successfully", "access_token": access_token}), 200


        return jsonify({'message': 'Invalid email or password'}), 401

    except Exception as e:
        return jsonify({"message": "Error logging in"}), 500


# add user to user table by admin (use admin login access token)
@app.route('/add_user', methods=['POST'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def add_user():
    try:
        current_admin_email = get_jwt_identity()

        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        new_user = User(username=username, email=email, password=password, Admin_id=admin.Admin_id,
                        created_at=datetime.now())

        db.session.add(new_user)
        db.session.commit()
        send_verification_email(new_user)

        return jsonify({"message": "User added successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Error adding user"}), 500


# update user to user table by admin (use admin login access token)
@app.route('/update_user', methods=['PUT'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def update_user():
    try:
        current_admin_email = get_jwt_identity()

        data = request.get_json()
        user_id = data.get('user_id')
        new_username = data.get('username')
        email = data.get('email')
        password = data.get('password')

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        user.username = new_username
        user.email = email
        user.password = password

        leaves = Leaves.query.filter_by(user_id=user_id).all()
        for leave in leaves:
            leave.username = new_username

        db.session.commit()

        attendance = Attendance.query.filter_by(user_id=user_id).all()
        for attendances in attendance:
            attendances.username = new_username

        db.session.commit()

        return jsonify({"message": "User updated successfully"}), 200
    except Exception as e:
        return jsonify({"message": "Error updating user"}), 500


# delete user by admin (use admin login access token)
@app.route('/admin/delete_user/<int:user_id>', methods=['DELETE'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def admin_delete_user(user_id):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        user_to_delete = User.query.filter_by(user_id=user_id, Admin_id=Admin.Admin_id).first()
        if not user_to_delete:
            return jsonify({'message': 'User not found or does not belong to the admin'}), 404

        related_leaves = Leaves.query.filter_by(user_id=user_id).all()
        for leave in related_leaves:
            db.session.delete(leave)

        related_attendance = Attendance.query.filter_by(user_id=user_id).all()
        for attendance in related_attendance:
            db.session.delete(attendance)

        db.session.delete(user_to_delete)
        db.session.commit()

        return jsonify({'message': 'User and related data deleted successfully'}), 200
    except Exception as e:
        return jsonify({"message": "Error deleting user and related data"}), 500


# get user by id (use userlogin access token)
@app.route("/getuser/<int:User_id>", methods=["GET"])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def getUserById(User_id):
    try:
        user = User.query.get_or_404(User_id)
        user_data = {
            "user_id": user.user_id,
            "username": user.username,
            "password": user.password,
            "email": user.email,
            "Admin_id": user.Admin_id,
            "created_at": str(user.created_at)
        }
        return jsonify(user_data)
    except Exception as e:

        return jsonify({"Error": "Can't able to get user", "Exception": str(e)})


# attendance logout (use attendance login access token)
@app.route('/attendance/logout', methods=['POST'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def logout():
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)

        if not user:
            return jsonify(message="User not found")

        latest_attendance = Attendance.query.filter_by(user_id=current_user_id).order_by(Attendance.id.desc()).first()

        if latest_attendance:
            latest_attendance.logout_time = datetime.now()
            latest_attendance.status = 'present'
            db.session.commit()
            return jsonify(message="Logout time updated successfully")
        else:
            return jsonify(message="No attendance record found for this user")

    except Exception as e:
        return jsonify(error=str(e))


# get all user from user table (use admin login access token)
@app.route('/get_all_users', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_all_users():
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        users = User.query.filter_by(user_id=User.user_id).all()

        users_data = []
        for user in users:
            user_info = {
                'user_id': user.user_id,
                'username': user.username,
                'email': user.email,
                "Admin_id": user.Admin_id,
                "created_at": str(user.created_at)

            }
            users_data.append(user_info)

        return jsonify({'users': users_data}), 200
    except Exception as e:
        return jsonify({"message": "Error retrieving users"}), 500


# apply leave (use userlogin access token)
@app.route('/apply_leave', methods=['POST'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def apply_leave():
    user_id = get_jwt_identity()
    data = request.get_json()
    try:
        from_date = data.get('from_date')
        to_date = data.get('to_date')
        reason = data.get('reason')
        # status = data.get('status')
        if not reason:
            return jsonify({'message': 'Reason is required'}), 400

        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404
        username = user.username


        leave = Leaves(
            user_id=user_id,
            username=username,
            from_date=from_date,
            to_date=to_date,
            reason=reason,
            status='pending'
        )
        db.session.add(leave)
        db.session.commit()
        send_leave_email(leave, user)
        return jsonify({"message": "Leave applied successfully"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": "Error applying leave"}), 500


# get all leave from leave table (use admin login access token)
@app.route('/get_all_leaves', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_all_leaves():
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        leaves = Leaves.query.filter_by(user_id=Leaves.user_id).all()

        leave_data = []
        for leave in leaves:
            leave_info = {
                'LeaveId': leave.LeaveId,
                'user_id': leave.user_id,
                'username': leave.username,
                'from_date': leave.from_date,
                'to_date': leave.to_date,
                'reason': leave.reason,
                'status': leave.status
            }
            leave_data.append(leave_info)

        return jsonify({'leaves': leave_data}), 200
    except Exception as e:
        return jsonify({"message": "Error retrieving leaves"}), 500


# get user leave by id (use userlogin access token)
@app.route('/user_leave/<int:user_id>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_user_leave(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        user_leave = Leaves.query.filter_by(user_id=user_id).all()
        leave_data = [
            {'LeaveId': leave.LeaveId, 'user_id': leave.user_id, 'username': leave.username,'from_date': leave.from_date, 'to_date': leave.to_date, 'reason': leave.reason,
             'status': leave.status} for leave in user_leave]
        return jsonify({'user_leave': leave_data}), 200
    except Exception as e:
        return jsonify({"message": "Error retrieving user leave"}), 500


# get all user attendance (use admin login access token)
@app.route('/attendance/all', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_all_attendance():
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        attendance_records = Attendance.query.join(User).filter(User.user_id == Attendance.user_id).all()

        attendance_data = []
        for record in attendance_records:
            attendance_info = {
                'user_id': record.user_id,
                'username': record.username,
                'login_time': record.login_time.strftime("%Y-%m-%d %H:%M:%S") if record.login_time else None,
                'logout_time': record.logout_time.strftime("%Y-%m-%d %H:%M:%S") if record.logout_time else None
            }
            attendance_data.append(attendance_info)

        return jsonify({'attendance': attendance_data}), 200
    except Exception as e:
        return jsonify({"message": "Error retrieving attendance"}), 500


# get attendance by id (use userlogin access token)
@app.route('/attendance/<int:user_id>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_attendance_by_user_id(user_id):
    try:
        attendance_records = Attendance.query.filter_by(user_id=user_id).all()

        if not attendance_records:
            return jsonify(message="No attendance records found for this user")

        attendance_list = []
        for record in attendance_records:
            attendance_list.append({
                'user_id': record.user_id,
                'username': record.username,
                'login_time': record.login_time.strftime("%Y-%m-%d %H:%M:%S") if record.login_time else None,
                'logout_time': record.logout_time.strftime("%Y-%m-%d %H:%M:%S") if record.logout_time else None
            })

        return jsonify(attendance_list)

    except Exception as e:
        return jsonify(error=str(e))


# --------------------------------------TASK 2-----------------------------------------------------

# route for admin to approve leave
@app.route('/approve_leave/<int:leave_id>', methods=['PUT'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def approve_leave(leave_id):
    try:
        current_admin_email = get_jwt_identity()


        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404


        leave = Leaves.query.get(leave_id)
        if not leave:
            return jsonify({'message': 'Leave request not found'}), 404


        leave.status = 'approved'
        db.session.commit()
        user = User.query.get(leave.user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        send_leave_approval_email(leave, user)

        return jsonify({'message': 'Leave request approved successfully'}), 200
    except Exception as e:
        return jsonify({"message": "Error approving leave"}), 500


# Route for admin to reject leave
@app.route('/reject_leave/<int:leave_id>', methods=['PUT'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def reject_leave(leave_id):
    try:
        current_admin_email = get_jwt_identity()


        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404


        leave = Leaves.query.get(leave_id)
        if not leave:
            return jsonify({'message': 'Leave request not found'}), 404


        leave.status = 'rejected'
        db.session.commit()
        user = User.query.get(leave.user_id)
        if not user:
            return jsonify({'message': 'User not found'}), 404

        send_leave_rejection_email(leave, user)

        return jsonify({'message': 'Leave request rejected successfully'}), 200
    except Exception as e:
        return jsonify({"message": "Error rejecting leave"}), 500


# absent user from and to date
@app.route('/absent_users_data', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_absent_users_data():
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404



        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')


        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')


        absent_users_query = Attendance.query.filter(
            func.date(Attendance.login_time) >= start_date.date(),
            func.date(Attendance.login_time) <= end_date.date(),
            Attendance.status == 'absent'
        )


        absent_users_count = absent_users_query.count()


        absent_users = absent_users_query.all()


        absent_users_data = []
        for user in absent_users:
            user_data = {
                'user_id': user.user_id,
                'username': user.username,
                'login_time': user.login_time.strftime("%Y-%m-%d %H:%M:%S"),
                'logout_time': user.logout_time.strftime("%Y-%m-%d %H:%M:%S") if user.logout_time else None,
                'status': user.status
            }
            absent_users_data.append(user_data)

        return jsonify({'absent_users_count': absent_users_count, 'absent_users': absent_users_data}), 200

    except Exception as e:
        return jsonify({"message": "Error fetching absent users data"}), 500


# Attendance count from date and to date
@app.route('/present_users_data', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_present_users_data():
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')


        if not start_date_str or not end_date_str:
            return jsonify({"message": "Start date and end date are required."}), 400


        start_date_str = start_date_str.strip()
        end_date_str = end_date_str.strip()


        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')


        present_users_query = Attendance.query.filter(
            func.date(Attendance.login_time) >= start_date.date(),
            func.date(Attendance.login_time) <= end_date.date(),
            Attendance.status == 'present'
        )


        present_users_count = present_users_query.count()


        present_users = present_users_query.all()


        present_users_data = []
        for user in present_users:
            user_data = {
                'user_id': user.user_id,
                'username': user.username,
                'login_time': user.login_time.strftime("%Y-%m-%d %H:%M:%S"),
                'logout_time': user.logout_time.strftime("%Y-%m-%d %H:%M:%S") if user.logout_time else None,
                'status': user.status
            }
            present_users_data.append(user_data)

        return jsonify({'present_users_count': present_users_count, 'present_users': present_users_data}), 200

    except ValueError as ve:
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD format.", "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"message": "Error fetching present users data"}), 500


# rejected leave per day count
@app.route('/rejected_leaves/<date>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_rejected_leaves(date):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        date_obj = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    formatted_date = date_obj.strftime('%d/%m/%Y')
    leaves = Leaves.query.filter(db.func.lower(Leaves.status) == 'rejected').filter(
        Leaves.from_date <= formatted_date).filter(Leaves.to_date >= formatted_date).all()

    rejected_leaves = []
    for leave in leaves:
        rejected_leaves.append({
            'LeaveId': leave.LeaveId,
            'user_id': leave.user_id,
            'username': leave.username,
            'from_date': leave.from_date,
            'to_date': leave.to_date,
            'reason': leave.reason,
            'status': leave.status
        })
    leaves_count = Leaves.query.filter(db.func.lower(Leaves.status) == 'rejected').filter(
        Leaves.from_date <= formatted_date).filter(Leaves.to_date >= formatted_date).count()

    return jsonify({'rejected_leaves': rejected_leaves, 'rejected_leave_count': leaves_count})


# Get count of pending leaves for a specific date
@app.route('/pending_leaves/<date>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_pending_leaves(date):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        date_obj = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    formatted_date = date_obj.strftime('%d/%m/%Y')
    leaves = Leaves.query.filter(db.func.lower(Leaves.status) == 'pending').filter(
        Leaves.from_date <= formatted_date).filter(Leaves.to_date >= formatted_date).all()

    pending_leaves = []
    for leave in leaves:
        pending_leaves.append({
            'LeaveId': leave.LeaveId,
            'user_id': leave.user_id,
            'username': leave.username,
            'from_date': leave.from_date,
            'to_date': leave.to_date,
            'reason': leave.reason,
            'status': leave.status
        })
    leaves_count = Leaves.query.filter(db.func.lower(Leaves.status) == 'pending').filter(
        Leaves.from_date <= formatted_date).filter(Leaves.to_date >= formatted_date).count()

    return jsonify({'pending_leaves': pending_leaves, 'pending_leave_count': leaves_count})


# Get count of approved leaves for a specific date
@app.route('/approved_leaves/<date>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_approved_leaves(date):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        date_obj = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    formatted_date = date_obj.strftime('%d/%m/%Y')
    leaves = Leaves.query.filter(db.func.lower(Leaves.status) == 'approved').filter(
        Leaves.from_date <= formatted_date).filter(Leaves.to_date >= formatted_date).all()

    approved_leaves = []
    for leave in leaves:
        approved_leaves.append({
            'LeaveId': leave.LeaveId,
            'user_id': leave.user_id,
            'username': leave.username,
            'from_date': leave.from_date,
            'to_date': leave.to_date,
            'reason': leave.reason,
            'status': leave.status
        })
    leaves_count = Leaves.query.filter(db.func.lower(Leaves.status) == 'approved').filter(
        Leaves.from_date <= formatted_date).filter(Leaves.to_date >= formatted_date).count()

    return jsonify({'approved_leaves': approved_leaves, 'approved_leave_count': leaves_count})


# Get  leaves count for a specific date
@app.route('/total_leaves/<date>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_total_leaves(date):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        date_obj = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    formatted_date = date_obj.strftime('%d/%m/%Y')
    leaves = Leaves.query.filter(db.func.lower(Leaves.status) == Leaves.status).filter(
        Leaves.from_date <= formatted_date).filter(Leaves.to_date >= formatted_date).all()

    all_leaves = []
    for leave in leaves:
        all_leaves.append({
            'LeaveId': leave.LeaveId,
            'user_id': leave.user_id,
            'username': leave.username,
            'from_date': leave.from_date,
            'to_date': leave.to_date,
            'reason': leave.reason,
            'status': leave.status
        })
    leaves_count = Leaves.query.filter(db.func.lower(Leaves.status) == Leaves.status).filter(
        Leaves.from_date <= formatted_date).filter(Leaves.to_date >= formatted_date).count()

    return jsonify({'all_leaves': all_leaves, 'all_leave_count': leaves_count})



# Pending Leave count from date to date
@app.route('/pending_leaves_data', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_pending_leaves_data():
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')


        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')


        pending_leaves_query = Leaves.query.filter(
            func.date(Leaves.from_date) >= start_date.date(),
            func.date(Leaves.to_date) <= end_date.date(),
            Leaves.status == 'pending'
        )


        pending_leaves_count = pending_leaves_query.count()


        pending_leaves = pending_leaves_query.all()


        pending_leaves_data = []
        for leave in pending_leaves:
            leave_data = {
                'LeaveId': leave.LeaveId,
                'user_id': leave.user_id,
                'username': leave.username,
                'from_date': leave.from_date,
                'to_date': leave.to_date,
                'reason': leave.reason,
                'status': leave.status
            }
            pending_leaves_data.append(leave_data)

        return jsonify({'pending_leaves': pending_leaves_data, 'pending_leaves_count': pending_leaves_count}), 200

    except Exception as e:
        return jsonify({"message": "Error fetching pending leaves data"}), 500


# Get Rejected leaves count from date and to date
@app.route('/rejected_leaves_data', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_rejected_leaves_data():
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')


        if not start_date_str or not end_date_str:
            return jsonify({"message": "Start date and end date are required."}), 400


        start_date_str = start_date_str.strip()
        end_date_str = end_date_str.strip()


        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')


        rejected_leaves_query = Leaves.query.filter(
            func.date(Leaves.from_date) >= start_date.date(),
            func.date(Leaves.to_date) <= end_date.date(),
            Leaves.status == 'rejected'
        )


        rejected_leaves_count = rejected_leaves_query.count()


        rejected_leaves_data = []
        for leave in rejected_leaves_query:
            leave_data = {
                'LeaveId': leave.LeaveId,
                'user_id': leave.user_id,
                'username': leave.username,
                'from_date': leave.from_date,
                'to_date': leave.to_date,
                'reason': leave.reason,
                'status': leave.status
            }
            rejected_leaves_data.append(leave_data)

        return jsonify({'rejected_leaves_count': rejected_leaves_count, 'rejected_leaves': rejected_leaves_data}), 200

    except ValueError as ve:
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD format.", "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"message": "Error fetching rejected leaves data"}), 500


# Leave count from date to date
@app.route('/total_leaves_data', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_total_leaves_data():
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')


        if not start_date_str or not end_date_str:
            return jsonify({"message": "Start date and end date are required."}), 400


        start_date_str = start_date_str.strip()
        end_date_str = end_date_str.strip()


        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')


        total_leaves_query = Leaves.query.filter(
            func.date(Leaves.from_date) >= start_date.date(),
            func.date(Leaves.to_date) <= end_date.date()
        )


        total_leaves = []
        for leave in total_leaves_query:
            leave_data = {
                'LeaveId': leave.LeaveId,
                'user_id': leave.user_id,
                'username': leave.username,
                'from_date': leave.from_date,
                'to_date': leave.to_date,
                'reason': leave.reason,
                'status': leave.status
            }
            total_leaves.append(leave_data)

        total_leaves_count = len(total_leaves)

        return jsonify({'total_leaves_count': total_leaves_count, 'total_leaves': total_leaves}), 200

    except ValueError as ve:
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD format.", "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"message": "Error fetching total leaves data"}), 500


# Attendance count per day
@app.route('/present_count/<date>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_present_count(date):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        date_obj = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    formatted_date = date_obj.strftime('%Y-%m-%d')


    present_data = Attendance.query.filter(
        func.date(Attendance.login_time) == formatted_date,
        Attendance.status == 'present'
    ).all()


    present_list = []
    for entry in present_data:
        present_info = {
            'user_id': entry.user_id,
            'username': entry.username,
            'login_time': entry.login_time.strftime("%Y-%m-%d %H:%M:%S"),
            'logout_time': entry.logout_time.strftime("%Y-%m-%d %H:%M:%S") if entry.logout_time else None,
            'status': entry.status
        }
        present_list.append(present_info)


    present_count = len(present_list)

    return jsonify({'present_count': present_count, 'present_data': present_list}), 200


# Absent count per day
@app.route('/absent_data/<date>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_absent_data(date):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        date_obj = datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD.'}), 400

    formatted_date = date_obj.strftime('%Y-%m-%d')


    absent_data = Attendance.query.filter(
        func.date(Attendance.login_time) == formatted_date,
        Attendance.status == 'absent'
    ).all()


    absent_list = []
    for absent_entry in absent_data:
        absent_info = {
            'user_id': absent_entry.user_id,
            'username': absent_entry.username,
            'login_time': absent_entry.login_time.strftime("%Y-%m-%d %H:%M:%S"),
            'logout_time': absent_entry.logout_time.strftime("%Y-%m-%d %H:%M:%S") if absent_entry.logout_time else None,
            'status': absent_entry.status
        }
        absent_list.append(absent_info)


    absent_count = len(absent_list)

    return jsonify({'absent_count': absent_count, 'absent_data': absent_list}), 200


# absent_count_by_id(from date and to date)
@app.route('/absent_count_by_id/<int:user_id>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_absent_count_by_id(user_id):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')


        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')


        absent_count = Attendance.query.filter_by(user_id=user_id).filter(
            Attendance.login_time >= start_date,
            Attendance.login_time <= end_date,
            Attendance.status == 'absent'
        ).count()


        absent_data = Attendance.query.filter_by(user_id=user_id).filter(
            Attendance.login_time >= start_date,
            Attendance.login_time <= end_date,
            Attendance.status == 'absent'
        ).all()


        absent_list = []
        for absent_entry in absent_data:
            absent_info = {
                'user_id': absent_entry.user_id,
                'username': absent_entry.username,
                'login_time': absent_entry.login_time.strftime("%Y-%m-%d %H:%M:%S"),
                'logout_time': absent_entry.logout_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if absent_entry.logout_time else None,
                'status': absent_entry.status
            }
            absent_list.append(absent_info)

        return jsonify({'absent_count': absent_count, 'absent_data': absent_list}), 200

    except Exception as e:
        return jsonify({"message": "Error fetching absent count for user"}), 500


# present count by user id and from date to date
@app.route('/present_count_by_id/<int:user_id>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_present_count_by_id(user_id):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')

        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

        present_count = Attendance.query.filter_by(user_id=user_id).filter(
            Attendance.login_time >= start_date,
            Attendance.login_time <= end_date,
            Attendance.status == 'present'
        ).count()

        present_data = Attendance.query.filter_by(user_id=user_id).filter(
            Attendance.login_time >= start_date,
            Attendance.login_time <= end_date,
            Attendance.status == 'present'
        ).all()


        present_list = []
        for present_entry in present_data:
            present_info = {
                'user_id': present_entry.user_id,
                'username': present_entry.username,
                'login_time': present_entry.login_time.strftime("%Y-%m-%d %H:%M:%S"),
                'logout_time': present_entry.logout_time.strftime(
                    "%Y-%m-%d %H:%M:%S") if present_entry.logout_time else None,
                'status': present_entry.status
            }
            present_list.append(present_info)

        return jsonify({'present_count': present_count, 'present_data': present_list}), 200

    except Exception as e:
        return jsonify({"message": "Error fetching present count for user"}), 500


# total leave count by id
@app.route('/total_leave_count_by_id/<int:user_id>', methods=['GET'])
@jwt_required()
@swag_from('swagger_doc/swagger.yaml')
def get_total_leave_count_by_id(user_id):
    try:
        current_admin_email = get_jwt_identity()

        admin = Admin.query.filter_by(Email=current_admin_email).first()
        if not admin:
            return jsonify({'message': 'Admin not found'}), 404

        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')


        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')


        total_leave_count = Leaves.query.filter_by(user_id=user_id).filter(
            func.date(Leaves.from_date) >= start_date.date(),
            func.date(Leaves.to_date) <= end_date.date()
        ).count()


        leave_data = Leaves.query.filter_by(user_id=user_id).filter(
            func.date(Leaves.from_date) >= start_date.date(),
            func.date(Leaves.to_date) <= end_date.date()
        ).all()

        # Process the leave data
        leave_list = []
        for leave_entry in leave_data:
            leave_info = {
                'LeaveId': leave_entry.LeaveId,
                'user_id': leave_entry.user_id,
                'username': leave_entry.username,
                'from_date': datetime.strptime(leave_entry.from_date, '%d/%m/%Y').strftime("%Y-%m-%d"),
                'to_date': datetime.strptime(leave_entry.to_date, '%d/%m/%Y').strftime("%Y-%m-%d"),
                'reason': leave_entry.reason,
                'status': leave_entry.status
            }
            leave_list.append(leave_info)

        return jsonify({'total_leave_count': total_leave_count, 'leave_data': leave_list}), 200

    except ValueError as ve:
        return jsonify({"message": "Invalid date format. Please use YYYY-MM-DD format.", "error": str(ve)}), 400
    except Exception as e:
        return jsonify({"message": "Error fetching total leave count for user"}), 500


def generate_swagger_yaml():
    paths = {}

    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            paths[str(rule)] = {
                'get': app.view_functions[rule.endpoint]._doc_,
                'post': app.view_functions[rule.endpoint]._doc_,
                'put': app.view_functions[rule.endpoint]._doc_,
                'delete': app.view_functions[rule.endpoint]._doc_,
            }

    swagger_yaml = {
        'openapi': '3.0.0',
        'info': {
            'title': 'Leave Management API',
            'description': 'API for managing leaves',
            'version': '1.0.0'
        },
        'paths': paths
    }

    with open('swagger.yaml', 'w') as file:
        yaml.dump(swagger_yaml, file)







if __name__ == '__main__':
    app.run(debug=True)