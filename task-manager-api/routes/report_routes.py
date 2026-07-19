from flask import Blueprint, request, jsonify
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from datetime import timedelta
from utils.helpers import calculate_percentage, utcnow

report_bp = Blueprint('reports', __name__)

@report_bp.route('/reports/summary', methods=['GET'])
def summary_report():

    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_categories = Category.query.count()

    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    critical_count = Task.query.filter_by(priority=1).count()
    high_count = Task.query.filter_by(priority=2).count()
    medium_count = Task.query.filter_by(priority=3).count()
    low_count = Task.query.filter_by(priority=4).count()
    minimal_count = Task.query.filter_by(priority=5).count()

    all_tasks = Task.query.all()
    overdue_count = 0
    overdue_list = []
    for task in all_tasks:
        if task.is_overdue():
            overdue_count = overdue_count + 1
            overdue_list.append({
                'id': task.id,
                'title': task.title,
                'due_date': str(task.due_date),
                'days_overdue': (utcnow() - task.due_date).days
            })

    seven_days_ago = utcnow() - timedelta(days=7)
    recent_tasks = Task.query.filter(Task.created_at >= seven_days_ago).count()

    recent_done = Task.query.filter(
        Task.status == 'done',
        Task.updated_at >= seven_days_ago
    ).count()

    users = User.query.all()
    user_stats = []
    for user in users:
        user_tasks = Task.query.filter_by(user_id=user.id).all()
        total = len(user_tasks)
        completed = 0
        for task in user_tasks:
            if task.status == 'done':
                completed = completed + 1
        user_stats.append({
            'user_id': user.id,
            'user_name': user.name,
            'total_tasks': total,
            'completed_tasks': completed,
            'completion_rate': calculate_percentage(completed, total)
        })

    report = {
        'generated_at': str(utcnow()),
        'overview': {
            'total_tasks': total_tasks,
            'total_users': total_users,
            'total_categories': total_categories,
        },
        'tasks_by_status': {
            'pending': pending,
            'in_progress': in_progress,
            'done': done,
            'cancelled': cancelled,
        },
        'tasks_by_priority': {
            'critical': critical_count,
            'high': high_count,
            'medium': medium_count,
            'low': low_count,
            'minimal': minimal_count,
        },
        'overdue': {
            'count': overdue_count,
            'tasks': overdue_list,
        },
        'recent_activity': {
            'tasks_created_last_7_days': recent_tasks,
            'tasks_completed_last_7_days': recent_done,
        },
        'user_productivity': user_stats,
    }

    return jsonify(report), 200

@report_bp.route('/reports/user/<int:user_id>', methods=['GET'])
def user_report(user_id):
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404

    tasks = Task.query.filter_by(user_id=user_id).all()

    total = len(tasks)
    done = 0
    pending = 0
    in_progress = 0
    cancelled = 0
    overdue = 0
    high_priority = 0

    for task in tasks:
        if task.status == 'done':
            done = done + 1
        elif task.status == 'pending':
            pending = pending + 1
        elif task.status == 'in_progress':
            in_progress = in_progress + 1
        elif task.status == 'cancelled':
            cancelled = cancelled + 1

        if task.priority <= 2:
            high_priority = high_priority + 1

        if task.is_overdue():
            overdue = overdue + 1

    report = {
        'user': {
            'id': user.id,
            'name': user.name,
            'email': user.email,
        },
        'statistics': {
            'total_tasks': total,
            'done': done,
            'pending': pending,
            'in_progress': in_progress,
            'cancelled': cancelled,
            'overdue': overdue,
            'high_priority': high_priority,
            'completion_rate': calculate_percentage(done, total)
        }
    }

    return jsonify(report), 200

@report_bp.route('/categories', methods=['GET'])
def get_categories():
    categories = Category.query.all()
    result = []
    for category in categories:
        cat_data = category.to_dict()
        cat_data['task_count'] = Task.query.filter_by(category_id=category.id).count()
        result.append(cat_data)
    return jsonify(result), 200

@report_bp.route('/categories', methods=['POST'])
def create_category():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    name = data.get('name')
    if not name:
        return jsonify({'error': 'Nome é obrigatório'}), 400

    category = Category()
    category.name = name
    category.description = data.get('description', '')
    category.color = data.get('color', '#000000')

    db.session.add(category)
    db.session.commit()
    return jsonify(category.to_dict()), 201

@report_bp.route('/categories/<int:cat_id>', methods=['PUT'])
def update_category(cat_id):
    category = db.session.get(Category, cat_id)
    if not category:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    if 'name' in data:
        category.name = data['name']
    if 'description' in data:
        category.description = data['description']
    if 'color' in data:
        category.color = data['color']

    db.session.commit()
    return jsonify(category.to_dict()), 200

@report_bp.route('/categories/<int:cat_id>', methods=['DELETE'])
def delete_category(cat_id):
    category = db.session.get(Category, cat_id)
    if not category:
        return jsonify({'error': 'Categoria não encontrada'}), 404

    db.session.delete(category)
    db.session.commit()
    return jsonify({'message': 'Categoria deletada'}), 200
