import logging
from flask import Blueprint, request, jsonify
from database import db
from models.task import Task
from models.user import User
from models.category import Category
from utils.helpers import process_task_data, DEFAULT_PRIORITY, calculate_percentage

logger = logging.getLogger(__name__)

task_bp = Blueprint('tasks', __name__)

@task_bp.route('/tasks', methods=['GET'])
def get_tasks():
    tasks = Task.query.all()
    result = []
    for task in tasks:
        task_data = task.to_dict()
        task_data['overdue'] = task.is_overdue()

        user = db.session.get(User, task.user_id) if task.user_id else None
        task_data['user_name'] = user.name if user else None

        category = db.session.get(Category, task.category_id) if task.category_id else None
        task_data['category_name'] = category.name if category else None

        result.append(task_data)

    return jsonify(result), 200

@task_bp.route('/tasks/<int:task_id>', methods=['GET'])
def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task:
        data = task.to_dict()
        data['overdue'] = task.is_overdue()
        return jsonify(data), 200
    else:
        return jsonify({'error': 'Task não encontrada'}), 404

@task_bp.route('/tasks', methods=['POST'])
def create_task():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    processed, error = process_task_data(data)
    if error:
        return jsonify({'error': error}), 400

    if 'title' not in processed:
        return jsonify({'error': 'Título é obrigatório'}), 400

    user_id = data.get('user_id')
    category_id = data.get('category_id')

    if user_id:
        user = db.session.get(User, user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 404

    if category_id:
        category = db.session.get(Category, category_id)
        if not category:
            return jsonify({'error': 'Categoria não encontrada'}), 404

    task = Task()
    task.title = processed['title']
    task.description = processed.get('description', '')
    task.status = processed.get('status', 'pending')
    task.priority = processed.get('priority', DEFAULT_PRIORITY)
    task.user_id = user_id
    task.category_id = category_id
    task.due_date = processed.get('due_date')
    if 'tags' in processed:
        task.tags = processed['tags']

    db.session.add(task)
    db.session.commit()
    logger.info("Task criada: %s - %s", task.id, task.title)
    return jsonify(task.to_dict()), 201

@task_bp.route('/tasks/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    data = request.get_json()
    if not data:
        return jsonify({'error': 'Dados inválidos'}), 400

    processed, error = process_task_data(data, existing_task=task)
    if error:
        return jsonify({'error': error}), 400

    if 'title' in processed:
        task.title = processed['title']
    if 'description' in processed:
        task.description = processed['description']
    if 'status' in processed:
        task.status = processed['status']
    if 'priority' in processed:
        task.priority = processed['priority']
    if 'due_date' in processed:
        task.due_date = processed['due_date']
    if 'tags' in processed:
        task.tags = processed['tags']

    if 'user_id' in data:
        if data['user_id']:
            user = db.session.get(User, data['user_id'])
            if not user:
                return jsonify({'error': 'Usuário não encontrado'}), 404
        task.user_id = data['user_id']

    if 'category_id' in data:
        if data['category_id']:
            category = db.session.get(Category, data['category_id'])
            if not category:
                return jsonify({'error': 'Categoria não encontrada'}), 404
        task.category_id = data['category_id']

    db.session.commit()
    logger.info("Task atualizada: %s", task.id)
    return jsonify(task.to_dict()), 200

@task_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if not task:
        return jsonify({'error': 'Task não encontrada'}), 404

    db.session.delete(task)
    db.session.commit()
    logger.info("Task deletada: %s", task_id)
    return jsonify({'message': 'Task deletada com sucesso'}), 200

@task_bp.route('/tasks/search', methods=['GET'])
def search_tasks():
    query = request.args.get('q', '')
    status = request.args.get('status', '')
    priority = request.args.get('priority', '')
    user_id = request.args.get('user_id', '')

    tasks = Task.query

    if query:
        tasks = tasks.filter(
            db.or_(
                Task.title.like(f'%{query}%'),
                Task.description.like(f'%{query}%')
            )
        )

    if status:
        tasks = tasks.filter(Task.status == status)

    if priority:
        tasks = tasks.filter(Task.priority == int(priority))

    if user_id:
        tasks = tasks.filter(Task.user_id == int(user_id))

    results = tasks.all()
    output = []
    for task in results:
        output.append(task.to_dict())

    return jsonify(output), 200

@task_bp.route('/tasks/stats', methods=['GET'])
def task_stats():
    total = Task.query.count()
    pending = Task.query.filter_by(status='pending').count()
    in_progress = Task.query.filter_by(status='in_progress').count()
    done = Task.query.filter_by(status='done').count()
    cancelled = Task.query.filter_by(status='cancelled').count()

    all_tasks = Task.query.all()
    overdue_count = sum(1 for task in all_tasks if task.is_overdue())

    stats = {
        'total': total,
        'pending': pending,
        'in_progress': in_progress,
        'done': done,
        'cancelled': cancelled,
        'overdue': overdue_count,
        'completion_rate': calculate_percentage(done, total)
    }

    return jsonify(stats), 200
