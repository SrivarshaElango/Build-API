from flask import Flask
import werkzeug
werkzeug.cached_property = werkzeug.utils.cached_property
from flask_restplus import Api, Resource, fields
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime, date
import requests

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='TodoMVC API',
    description='A simple TodoMVC API',
)

ns = api.namespace('todos', description='TODO operations')

todo = api.model('Todo', {
    'id': fields.Integer(readonly=True, description='The task unique identifier'),
    'task': fields.String(required=True, description='The task details'),
    'due by': fields.Date(required=True, description='Date when this task should be finished'),
    'status': fields.String(description='Current status of task', default='Not Started')
})

stat_val = ['Not Started', 'In Progress', 'Finished']

class TodoDAO(object):
    def __init__(self):
        self.counter = 0
        self.todos = []

    def get(self, id):
        for todo in self.todos:
            if todo['id'] == id:
                return todo
        api.abort(404, "Todo {} doesn't exist".format(id))

    def get_due(self, due):
        t=[]
        f=0
        for todo in self.todos:
            if due in todo['due by']:
                f=1
                t.append(todo)
        if f==1:
            return t
        api.abort(404, "Todo due on {} doesn't exist".format(due))

    def get_overdue(self):
        t=[]
        f=0
        d1=date.today()
        for todo in self.todos:
            d2=datetime.strptime(todo['due by'],'%Y-%m-%d').date()
            if d2<d1 and todo['status']!='Finished':
                f=1
                t.append(todo)
        if f==1:
            return t
        api.abort(404, "Overdue todos don't exist")
        
    def get_finished(self):
        t=[]
        f=0
        for todo in self.todos:
            if todo['status']=='Finished':
                f=1
                t.append(todo)
        if f==1:
            return t
        api.abort(404, "Completed/Finished todos don't exist")

    def create(self, data):
        if 'status' in data.keys() and data['status'] not in stat_val:
            return
        todo = data
        todo['id'] = self.counter = self.counter + 1
        self.todos.append(todo)
        return todo

    def update(self, id, data):
        if 'status' in data.keys() and data['status'] not in stat_val:
            return
        todo = self.get(id)
        todo.update(data)
        return todo

    def delete(self, id):
        todo = self.get(id)
        self.todos.remove(todo)


DAO = TodoDAO()
DAO.create({'task': 'Build an API', 'due by': '2021-02-15'})
DAO.create({'task': '?????', 'due by': '2021-10-10', 'status': 'Finished'})
DAO.create({'task': 'profit!', 'due by': '2021-08-20', 'status': 'In Progress'})

@ns.route('/')
class TodoList(Resource):
    '''Shows a list of all todos, and lets you POST to add new tasks'''
    @ns.doc('list_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all tasks'''
        return DAO.todos

    @ns.doc('create_todo')
    @ns.expect(todo)
    @ns.marshal_with(todo, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.create(api.payload), 201

@ns.route('/<string:due_date>')
@ns.response(404, 'Todo not found')
@ns.param('due_date', 'The due by date of task')
class TodoDue(Resource):
    '''Shows tasks due on a particular date'''
    @ns.doc('get_due_todos')
    @ns.marshal_list_with(todo)
    def get(self, due_date):
        '''List all tasks due on the given date'''
        return DAO.get_due(due_date)

@ns.route('/overdue')
class TodoOverdue(Resource):
    '''Lists overdue tasks'''
    @ns.doc('get_overdue_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all overdue tasks'''
        return DAO.get_overdue()

@ns.route('/finished')
class TodoFinished(Resource):
    '''Lists completed/finished tasks'''
    @ns.doc('get_finished_todos')
    @ns.marshal_list_with(todo)
    def get(self):
        '''List all finished tasks'''
        return DAO.get_finished()

@ns.route('/<int:id>')
@ns.response(404, 'Todo not found')
@ns.param('id', 'The task identifier')
class Todo(Resource):
    '''Show a single todo item and lets you delete them'''
    @ns.doc('get_todo')
    @ns.marshal_with(todo)
    def get(self, id):
        '''List a task given its identifier'''
        return DAO.get(id)

    @ns.doc('delete_todo')
    @ns.response(204, 'Todo deleted')
    def delete(self, id):
        '''Delete a task given its identifier'''
        DAO.delete(id)
        return '', 204

    @ns.expect(todo)
    @ns.marshal_with(todo)
    def put(self, id):
        '''Update a task given its identifier'''
        return DAO.update(id, api.payload)

if __name__ == '__main__':
    app.run(debug=True)
