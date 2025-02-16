from flask import Flask, render_template, request, redirect, url_for, flash, send_file, jsonify
import firebase_admin
from firebase_admin import credentials, firestore
from datetime import datetime, timedelta
from bill_generator import BillGenerator  # Assuming you have this module
import pytz

# Initialize Firebase Admin with your credentials
cred = credentials.Certificate({
    "type": "service_account",
    "project_id": "bill-ed04a",
    "private_key_id": "4e718267369dbe28312e0893bf6814d1ec09d3a0",
    "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQDFhZTIPjIPeUgR\nRzj15CW7cDx1O677YLxn3tltmpQ3vOfeEcbZVygHDON5GFpD08mFi8oEHLV1gk4D\n+Zb5ZpG7bqRphLSPfU5aP8iKbhqw/mtY/0DTbtd1dbh/JS3HxgD0gh5j4O8tOMpk\nVu2L80jpdMheEO3KaTLoIV/NlMDnKt81pZ3bUOOdTsQewpY0ZefFP71e256U/7c2\np2NJmJv7crI15psaCdObkspviESoS9onrv6FX+BlJKJUYUUC8E7YUNOeU80PJEax\n2gBfW5315mmfqwyRN94cAiPO0qssTzr01npbXuwP3GCnkrduDDImAmplWupzUfP6\n9xUWLTu/AgMBAAECggEAGbzYmz3He3lb6QHKgU1I7A3+7W5pKaZRm936SlbhyLWG\nfSBR3zuFIri3jK2eAsfpCCF5TGSKnJTtzNohUGmLbyHxWIfgmJtFB2uCRSTTDjce\nDnW29mteC0HbWENO84DF2mvOFp5WbCJsn6XYGZa07H65e9BhkTDOCli29BcrCl6y\nazUrNRcboN2aNNoQOQEw7AyM4quoMEszsTIBI+y9Ykh+rw5c11KiP6Pc/s9FSTLV\nFKDGKFWXw/imElqdIfUHamCg38OaMb6DqTXUBDdAS460rm4LFwD3DGoUi2nJ4O2S\nPCAEAhJaG7/irm/S1Tyj4irVV/ZRMS24b7jN0QJucQKBgQD8tCsDOgW0Rk2izWud\nt44QiECjfUKm8Ep89q6Whg4VQCci9uINVhBWrOvLhC9d9Gph1fmNkdWv4TpMPjtb\nn+jquzCSlhVT6oQy8UhZhByi30vaJfyNgEbWIWfsLHm4k8OzcgKdin88lpqW9i5x\no968KdMp8xoU7BzVriVVQn4aaQKBgQDIGSYTBd6dK0zIJnkz+LLj8Q8FcJXLP3D9\nFVe1l9jeb5Myh0hi8l2qoU5utMegSnSXqX96Sohgu4qqfmj/Ta4L0704USAqvakU\nDN4eRDhXJU2FPSUSoBBL4IxCSA3xzhJiZc/Fh9PCRtMY2sF+zj2JC/Yb3A4OoYK2\nWpykgLVP5wKBgAzSI0CFqBZuXq/81hHpZybFkun4h/IqTM0sQs1WPc6sM5AdkHh2\nvlt3aHsp2LFenisajQ+2r2298pQ9sAtFAK8wEhXN0YUxZ8Wh4jbQchd9Vr7ZoIeZ\nU363sSsVUpOfw5UOGr3dcfkj9vHjyZVwZ/OJ97GwKMmY9RmOPUynE/jJAoGAdJSq\naTTnQXzjzE0WGqCQYVumG84/h95bjyhrJKLmuJobEbpeA0AgMHSwxLFRCWO30FDx\ns6dPE8TQgosJ041HlR51RSWG7z/3DXZ9xvaKOMPECZfZTKOzOvIF5ewjK7mbXnbg\n+b4sMymefgGd8KpqkblFV2/7RKz3AhWC5BkVCgsCgYBcMZoMn7zkniH4DFYhv4X8\nrCD6PWQYifJQ7LY3/czK5scQ01ds8Lp9HvEmzR+YuvSPg2aCY97O2vlx6sEwO78N\nmr0VI8RO0lbVschLQ49rEVm+Il3Yl5wnT7BYixD+0PA8bT2SWEetRs5qA0uqKafI\nxPMPgBes+otgNRMEPzogsQ==\n-----END PRIVATE KEY-----\n",
    "client_email": "firebase-adminsdk-fbsvc@bill-ed04a.iam.gserviceaccount.com",
    "client_id": "105817808385211108883",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-fbsvc%40bill-ed04a.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com"
})

# Initialize Firebase
firebase_admin.initialize_app(cred)
db = firestore.client()

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if request.method == 'POST':
        try:
            # Check if customer ID already exists
            customer_id = str(request.form['customer_id'])
            existing_bills = db.collection('bills').where('customer_id', '==', customer_id).stream()
            
            # Convert to list to check if any bills exist
            existing_bills_list = list(existing_bills)
            if existing_bills_list:
                # Get the first bill to get customer details
                existing_customer = existing_bills_list[0].to_dict()
                return {
                    'status': 'error',
                    'message': 'Customer ID already exists',
                    'customer': {
                        'name': existing_customer['customer_name'],
                        'phone': existing_customer['phone'],
                        'id': existing_customer['customer_id']
                    }
                }, 400
            
            # If customer ID is unique, proceed with bill creation
            doc_ref = db.collection('bills').document()
            
            # Calculate balance
            total_amount = float(request.form['total_amount'])
            amount_paid = float(request.form['amount_paid'])
            balance = total_amount - amount_paid
            
            # Prepare billing data
            billing_data = {
                'customer_id': customer_id,
                'customer_name': str(request.form['customer_name']),
                'phone': str(request.form['phone']) if request.form['phone'] else None,
                'tree_id': str(request.form['tree_id']),
                'tree_measurement': str(request.form['tree_measurement']),
                'tree_quantity': int(request.form['tree_quantity']) if request.form['tree_quantity'] else 1,
                'total_amount': total_amount,
                'amount_paid': amount_paid,
                'balance': balance,
                'timestamp': firestore.SERVER_TIMESTAMP,
                'bill_id': doc_ref.id,
                'status': 'active'
            }

            doc_ref.set(billing_data)
            return {'status': 'success', 'message': 'Bill saved successfully!'}, 200
            
        except Exception as e:
            print(f"Error saving to Firestore: {e}")
            return {'status': 'error', 'message': str(e)}, 500

    return render_template('billing.html')

# Add the new bills route here
@app.route('/bills')
def bills():
    try:
        # Get all bills from Firestore
        bills_ref = db.collection('bills').order_by('timestamp', direction=firestore.Query.DESCENDING)
        bills = bills_ref.stream()
        bills_list = []
        for bill in bills:
            bill_data = bill.to_dict()
            # Convert timestamp to readable format
            if bill_data.get('timestamp'):
                bill_data['date'] = bill_data['timestamp'].strftime('%d/%m/%Y')
            bills_list.append(bill_data)
        return render_template('bills.html', bills=bills_list)
    except Exception as e:
        print(f"Error fetching bills: {e}")
        flash('Error fetching bills')
        return redirect(url_for('home'))

# Add the edit bill route here
@app.route('/edit_bill/<string:bill_id>', methods=['GET', 'POST'])
def edit_bill(bill_id):
    try:
        bill_ref = db.collection('bills').document(bill_id)
        
        if request.method == 'POST':
            # Calculate new balance
            total_amount = float(request.form['total_amount'])
            amount_paid = float(request.form['amount_paid'])
            balance = total_amount - amount_paid
            
            # Update bill data
            bill_data = {
                'customer_id': str(request.form['customer_id']),
                'customer_name': str(request.form['customer_name']),
                'phone': str(request.form['phone']),
                'tree_id': str(request.form['tree_id']),
                'tree_measurement': str(request.form['tree_measurement']),
                'tree_quantity': int(request.form['tree_quantity']) if request.form['tree_quantity'] else 1,
                'total_amount': float(total_amount),
                'amount_paid': float(amount_paid),
                'balance': float(balance),
                'last_edited': firestore.SERVER_TIMESTAMP
            }
            
            # Update the document
            bill_ref.update(bill_data)
            
            flash('Bill updated successfully!')
            return redirect(url_for('bills'))
        
        # GET request - show edit form
        bill = bill_ref.get()
        if bill.exists:
            return render_template('editbill.html', bill=bill.to_dict())
        else:
            flash('Bill not found!')
            return redirect(url_for('bills'))
            
    except Exception as e:
        print(f"Error updating bill: {e}")
        flash(f'Error: {str(e)}')
        return redirect(url_for('bills'))

# Add the download route
@app.route('/download_bill/<string:bill_id>')
def download_bill_route(bill_id):
    try:
        # Get bill data from Firestore
        bill_ref = db.collection('bills').document(bill_id)
        bill = bill_ref.get()
        
        if not bill.exists:
            flash('Bill not found!')
            return redirect(url_for('bills'))
            
        bill_data = bill.to_dict()
        
        # Format the timestamp to date string
        if bill_data.get('timestamp'):
            bill_data['date'] = bill_data['timestamp'].strftime('%d/%m/%Y')
        else:
            bill_data['date'] = datetime.datetime.now().strftime('%d/%m/%Y')
        
        # Generate PDF
        generator = BillGenerator()
        pdf_path = generator.generate_bill(bill_data)
        
        # Send file to user
        return send_file(
            pdf_path,
            as_attachment=True,
            download_name=f"bill_{bill_id}.pdf"
        )
        
    except Exception as e:
        print(f"Error generating bill: {e}")
        flash('Error generating bill')
        return redirect(url_for('bills'))

# Add customers route
@app.route('/customers')
def customers():
    try:
        # Get all bills from Firestore
        bills_ref = db.collection('bills').stream()
        
        # Create a dictionary to store unique customers
        customers_dict = {}
        
        # Extract unique customers from bills
        for bill in bills_ref:
            bill_data = bill.to_dict()
            customer_id = bill_data.get('customer_id')
            
            if customer_id not in customers_dict:
                customers_dict[customer_id] = {
                    'customer_id': customer_id,
                    'customer_name': bill_data.get('customer_name'),
                    'phone': bill_data.get('phone'),
                    'total_bills': 1,
                    'total_balance': bill_data.get('balance', 0)
                }
            else:
                customers_dict[customer_id]['total_bills'] += 1
                customers_dict[customer_id]['total_balance'] += bill_data.get('balance', 0)
        
        # Convert dictionary to list
        customers_list = list(customers_dict.values())
        
        return render_template('customers.html', customers=customers_list)
    except Exception as e:
        print(f"Error fetching customers: {e}")
        flash('Error fetching customers')
        return redirect(url_for('home'))

# Add customer lookup endpoint
@app.route('/get_customer')
def get_customer():
    try:
        search_by = request.args.get('searchBy')
        value = request.args.get('value')
        
        if not search_by or not value:
            return jsonify({'status': 'error', 'message': 'Missing parameters'}), 400

        # Debug logging
        print(f"Search request - searchBy: {search_by}, value: {value}")

        if search_by == 'id':
            customer_id = str(value).strip()
            print(f"Searching for customer_id: {customer_id}")
            
            bills = list(db.collection('bills')
                        .where('customer_id', '==', customer_id)
                        .limit(1)
                        .stream())
            
            print(f"Found {len(bills)} matching records for ID search")
        else:
            value = str(value).strip()
            print(f"Searching for customer_name: {value}")
            
            bills = list(db.collection('bills')
                        .where('customer_name', '==', value)
                        .limit(1)
                        .stream())
            
            print(f"Found {len(bills)} matching records for name search")

        if bills:
            customer_data = bills[0].to_dict()
            print(f"Found customer data: {customer_data}")
            response_data = {
                'status': 'success',
                'customer': {
                    'id': customer_data['customer_id'],
                    'name': customer_data['customer_name'],
                    'phone': customer_data.get('phone', '')
                }
            }
            print(f"Sending response: {response_data}")
            return jsonify(response_data)
        
        print("No matching records found")
        return jsonify({'status': 'success', 'customer': None})
        
    except Exception as e:
        print(f"Error in get_customer: {str(e)}")
        return jsonify({'status': 'error', 'message': str(e)}), 500

# Add tree management routes
@app.route('/trees')
def trees():
    try:
        # Get all trees from trees collection
        trees_ref = db.collection('trees').order_by('tree_id').stream()
        trees_dict = {tree.to_dict()['tree_id']: tree.to_dict() for tree in trees_ref}
        
        # Get trees from bills collection
        bills_ref = db.collection('bills').stream()
        
        # Update tree information from bills
        for bill in bills_ref:
            bill_data = bill.to_dict()
            tree_id = bill_data.get('tree_id')
            
            if tree_id:
                if tree_id not in trees_dict:
                    # Add new tree from bill
                    trees_dict[tree_id] = {
                        'tree_id': tree_id,
                        'size': bill_data.get('tree_measurement', 'N/A'),
                        'status': 'sold',
                        'customer_name': bill_data.get('customer_name'),
                        'bill_date': bill_data.get('timestamp'),
                        'bill_id': bill_data.get('bill_id'),
                        'amount': bill_data.get('total_amount')
                    }
                else:
                    # Update existing tree status if it was sold
                    trees_dict[tree_id].update({
                        'status': 'sold',
                        'customer_name': bill_data.get('customer_name'),
                        'bill_date': bill_data.get('timestamp'),
                        'bill_id': bill_data.get('bill_id'),
                        'amount': bill_data.get('total_amount')
                    })
        
        # Convert dictionary to list and sort by tree_id
        trees_list = list(trees_dict.values())
        trees_list.sort(key=lambda x: x['tree_id'])
        
        return render_template('trees.html', trees=trees_list)
    except Exception as e:
        print(f"Error fetching trees: {e}")
        flash('Error fetching trees')
        return redirect(url_for('home'))

@app.route('/add_tree', methods=['POST'])
def add_tree():
    try:
        # Create new tree document
        doc_ref = db.collection('trees').document()
        
        tree_data = {
            'tree_id': str(request.form['tree_id']),
            'size': str(request.form['size']),
            'description': str(request.form['description']),
            'status': 'available',
            'timestamp': firestore.SERVER_TIMESTAMP,
            'document_id': doc_ref.id
        }
        
        # Add to Firestore
        doc_ref.set(tree_data)
        
        flash('Tree added successfully!')
        return redirect(url_for('trees'))
    except Exception as e:
        print(f"Error adding tree: {e}")
        flash(f'Error: {str(e)}')
        return redirect(url_for('trees'))

@app.route('/get_customer_bills/<customer_id>')
def get_customer_bills(customer_id):
    try:
        bills = db.collection('bills').where('customer_id', '==', customer_id).stream()
        bills_list = [bill.to_dict() for bill in bills]
        return jsonify(bills_list)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/analytics')
def analytics():
    try:
        # Fetch all bills
        bills_ref = db.collection('bills').stream()
        bills = [bill.to_dict() for bill in bills_ref]
        
        # Initialize dictionaries for aggregation
        daily = {}
        weekly = {}
        monthly = {}
        
        # Define timezone
        tz = pytz.timezone('Asia/Kolkata')  # Adjust to your timezone
        
        for bill in bills:
            timestamp = bill.get('timestamp')
            if not timestamp:
                continue
            dt = timestamp.astimezone(tz)
            date_str = dt.strftime('%Y-%m-%d')
            
            # Daily aggregation
            daily[date_str] = daily.get(date_str, 0) + bill.get('total_amount', 0)
            
            # Weekly aggregation (ISO week number)
            year, week, _ = dt.isocalendar()
            week_str = f"{year}-W{week}"
            weekly[week_str] = weekly.get(week_str, 0) + bill.get('total_amount', 0)
            
            # Monthly aggregation
            month_str = dt.strftime('%Y-%m')
            monthly[month_str] = monthly.get(month_str, 0) + bill.get('total_amount', 0)
        
        # Sort the data
        daily_sorted = dict(sorted(daily.items()))
        weekly_sorted = dict(sorted(weekly.items()))
        monthly_sorted = dict(sorted(monthly.items()))
        
        return render_template('analytics.html',
                               daily=daily_sorted,
                               weekly=weekly_sorted,
                               monthly=monthly_sorted)
    except Exception as e:
        print(f"Error fetching analytics data: {e}")
        flash('Error fetching analytics data')
        return redirect(url_for('home'))

@app.route('/api/analytics')
def api_analytics():
    try:
        # Fetch all bills
        bills_ref = db.collection('bills').stream()
        bills = [bill.to_dict() for bill in bills_ref]
        
        # Initialize dictionaries for aggregation
        daily = {}
        weekly = {}
        monthly = {}
        
        # Define timezone
        tz = pytz.timezone('Asia/Kolkata')  # Adjust to your timezone
        
        for bill in bills:
            timestamp = bill.get('timestamp')
            if not timestamp:
                continue
            dt = timestamp.astimezone(tz)
            date_str = dt.strftime('%Y-%m-%d')
            
            # Daily aggregation
            daily[date_str] = daily.get(date_str, 0) + bill.get('total_amount', 0)
            
            # Weekly aggregation (ISO week number)
            year, week, _ = dt.isocalendar()
            week_str = f"{year}-W{week}"
            weekly[week_str] = weekly.get(week_str, 0) + bill.get('total_amount', 0)
            
            # Monthly aggregation
            month_str = dt.strftime('%Y-%m')
            monthly[month_str] = monthly.get(month_str, 0) + bill.get('total_amount', 0)
        
        # Sort the data
        daily_sorted = dict(sorted(daily.items()))
        weekly_sorted = dict(sorted(weekly.items()))
        monthly_sorted = dict(sorted(monthly.items()))
        
        return jsonify({
            'daily': daily_sorted,
            'weekly': weekly_sorted,
            'monthly': monthly_sorted
        })
    except Exception as e:
        print(f"Error fetching analytics data: {e}")
        return jsonify({'error': 'Error fetching analytics data'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)