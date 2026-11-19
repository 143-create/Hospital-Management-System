import unittest
from unittest.mock import patch
from app import app, db, seed_initial_doctors, User

class HospitalSystemTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['WTF_CSRF_ENABLED'] = False
        self.client = app.test_client()

        with app.app_context():
            db.drop_all()
            db.create_all()
            seed_initial_doctors()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_01_public_pages(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/login')
        self.assertEqual(res.status_code, 200)

        res = self.client.get('/register')
        self.assertEqual(res.status_code, 200)

    def test_02_protected_pages_unauthenticated(self):
        for route in ['/dashboard', '/patients', '/doctors', '/prescriptions', '/billing']:
            res = self.client.get(route)
            self.assertEqual(res.status_code, 302, f"Route {route} should redirect when unauthenticated")

    @patch("app.send_otp_email")
    def test_03_auth_flow_and_name_preservation(self, mock_send_email):
        # Step 1: Send OTP for registration (SMTP mocked for unit test)
        res = self.client.post('/api/auth/send-otp', json={
            "name": "Jane Doe",
            "email": "janedoe@example.com",
            "phone": "1234567890",
            "password": "securepassword123",
            "role": "Patient"
        })
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data["status"], "success")
        mock_send_email.assert_called_once()

        # Step 2: Resend OTP without providing name (ensures name is NOT overwritten)
        res_resend = self.client.post('/api/auth/send-otp', json={
            "email": "janedoe@example.com"
        })
        self.assertEqual(res_resend.status_code, 200)

        with app.app_context():
            user = User.query.filter_by(email="janedoe@example.com").first()
            self.assertEqual(user.name, "Jane Doe", "Name should NOT be overwritten with 'User' on OTP resend")
            new_otp = user.otp
            self.assertIsNotNone(new_otp)

        # Step 3: Verify OTP
        res_verify = self.client.post('/api/auth/verify-otp', json={
            "email": "janedoe@example.com",
            "otp": new_otp
        })
        self.assertEqual(res_verify.status_code, 200)

        # Step 4: Login with verified user
        res_login = self.client.post('/api/auth/login', json={
            "email": "janedoe@example.com",
            "password": "securepassword123"
        })
        self.assertEqual(res_login.status_code, 200)

    def test_04_authenticated_operations(self):
        with self.client.session_transaction() as sess:
            sess['user_email'] = 'admin@carepulse.com'
            sess['user_name'] = 'Admin Staff'
            sess['user_role'] = 'Staff'

        # Test Doctors Directory (seeded)
        res_docs = self.client.get('/api/doctors')
        self.assertEqual(res_docs.status_code, 200)
        docs = res_docs.get_json()
        self.assertGreaterEqual(len(docs), 5, "Doctors should be seeded automatically")

        # Test Appointment Booking
        res_appt = self.client.post('/api/appointments', json={
            "patient_name": "Alice Smith",
            "appointment_date": "2026-11-20",
            "time_slot": "09:00 AM - 10:00 AM",
            "doctor_id": docs[0]["id"],
            "doctor_name": docs[0]["name"]
        })
        self.assertEqual(res_appt.status_code, 200)
        self.assertEqual(res_appt.get_json()["status"], "success")

        # Test Patient Registration and Pagination
        res_pat = self.client.post('/api/patients', json={
            "name": "Alice Smith",
            "department": "Cardiology",
            "age": 42,
            "gender": "Female",
            "phone": "555-0199"
        })
        self.assertEqual(res_pat.status_code, 200)

        res_pat_list = self.client.get('/api/patients?page=1&limit=5')
        self.assertEqual(res_pat_list.status_code, 200)
        p_data = res_pat_list.get_json()
        self.assertGreaterEqual(p_data["total_records"], 1)

        # Test Prescriptions creation & retrieval
        res_rx = self.client.post('/api/prescriptions', json={
            "patient_name": "Alice Smith",
            "details": "Prescribing Doctor: Dr. Sarah Jenkins\nDiagnosis: Hypertension\nMedicines: Lisinopril 10mg"
        })
        self.assertEqual(res_rx.status_code, 200)

        res_rx_list = self.client.get('/api/prescriptions')
        self.assertEqual(res_rx_list.status_code, 200)
        self.assertGreaterEqual(len(res_rx_list.get_json()), 1)

        # Test Billing Creation and Payment
        res_bill = self.client.post('/api/billing', json={
            "patient_name": "Alice Smith",
            "amount": 250.00
        })
        self.assertEqual(res_bill.status_code, 200)
        bill_id = res_bill.get_json()["id"]

        res_pay = self.client.post(f'/api/billing/pay/{bill_id}')
        self.assertEqual(res_pay.status_code, 200)

        # Test Analytics
        res_analytics = self.client.get('/api/analytics')
        self.assertEqual(res_analytics.status_code, 200)
        a_data = res_analytics.get_json()
        self.assertGreaterEqual(a_data["metrics"]["total_revenue"], 250.00)

if __name__ == '__main__':
    unittest.main()