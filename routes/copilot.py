from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from services.copilot_service import copilot_service

copilot_bp = Blueprint('copilot', __name__)

@copilot_bp.route('/copilot', methods=['GET'])
@login_required
def index():
    return render_template('copilot.html')

@copilot_bp.route('/api/copilot', methods=['POST'])
@login_required
def ask_copilot():
    data = request.get_json() or {}
    query_text = data.get('query', '').strip()
    
    if not query_text:
        return jsonify({'success': False, 'message': 'Query cannot be empty.'}), 400

    result = copilot_service.process_query(current_user, query_text)
    return jsonify(result)
