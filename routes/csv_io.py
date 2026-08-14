from flask import Blueprint, render_template, request, jsonify, Response
from flask_login import login_required, current_user
from models import Expense
from services.csv_service import csv_service

csv_bp = Blueprint('csv_io', __name__)

@csv_bp.route('/import-export', methods=['GET'])
@login_required
def index():
    return render_template('import_export.html')

@csv_bp.route('/api/import', methods=['POST'])
@login_required
def import_csv():
    if 'file' not in request.files:
        return jsonify({'success': False, 'message': 'No CSV file provided in upload.'}), 400

    file = request.files['file']
    if not file or file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected.'}), 400

    if not file.filename.lower().endswith('.csv'):
        return jsonify({'success': False, 'message': 'Only .csv files are supported.'}), 400

    user_expenses = Expense.query.filter_by(user_id=current_user.id).all()
    result = csv_service.process_csv_import(file.stream, current_user.id, user_expenses)

    if not result.get('success'):
        return jsonify({'success': False, 'message': result.get('error', 'CSV Import failed.')}), 400

    return jsonify({
        'success': True,
        'message': f"Imported {result['imported']} transactions successfully!",
        'stats': {
            'imported': result['imported'],
            'skipped': result['skipped'],
            'duplicates': result['duplicates'],
            'invalid': result['invalid'],
            'total_rows': result['total_rows']
        }
    })

@csv_bp.route('/api/export', methods=['GET'])
@login_required
def export_csv():
    user_expenses = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.date.desc()).all()
    csv_data = csv_service.export_expenses_csv(user_expenses)

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename=personal_expenses_export.csv'
        }
    )
