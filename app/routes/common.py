from flask import Blueprint, jsonify
from app.utils.subjects import get_all_subjects

common_bp = Blueprint('common', __name__)

@common_bp.route('/subjects', methods=['GET'])
def get_subjects():
    """
    Get the list of structured subjects categories.
    """
    return jsonify(get_all_subjects()), 200
