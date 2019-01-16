import tornado.ioloop
import tornado.web
import json
import os
import model as model
import peewee as pw
from playhouse.shortcuts import model_to_dict
import playhouse.db_url
import datetime

db = playhouse.db_url.connect(os.environ.get('EMPDATABASE'))

def converter(obj):
    if isinstance(obj, datetime.date):
        return obj.__str__()


def is_date_correct(date):
    try:
        birthday = datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        return False
    return True

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.redirect(r"/index.html")


class EmployeesListHandler(tornado.web.RequestHandler):
    def get(self):
        employees = model.Employee.select()
        emps_data = []
        for emp in employees:
            emps_data.append({'id': emp.id, 
            'name': emp.name, 
            'birthday': emp.birthday.__str__(),
            'sex': emp.sex})
        self.write({'employees': emps_data})

    def post(self):
        employee = json.loads(self.request.body)
        name = employee['name']
        sex = 0
        if 'sex' in employee:
            sex = int(employee['sex'])
        birthday = datetime.datetime.strptime(employee['birthday'], '%Y-%m-%d')
        emp = model.add_employee(name, birthday, sex)
        self.set_status(201)
        self.write({'Location': 'http://localhost:8888/api/employees/{0}'.format(emp.id)})


class EmployeesListHandlerErrorChecking(EmployeesListHandler):
    def get(self):
        super(EmployeesListHandlerErrorChecking, self).get()
    
    def post(self):
        try:
            employee = json.loads(self.request.body)
            if 'name' not in employee:
                self.set_status(400)
                self.write({'error': {
                    'code': 'MissingArgument',
                    'message': 'name should be specified'
                }})
                return

            if 'birthday' not in employee:
                self.set_status(400)
                self.write({'error': {
                    'code': 'MissingArgument',
                    'message': 'birthday should be specified'
                }})
                return
            
            if not is_date_correct(employee['birthday']):
                self.set_status(500)
                self.write({'error' :{
                    'code': 'BadArguments',
                    'message': 'date should be in YYYY-mm-dd format'
                }})
                return
            
            sex = 0
            if 'sex' in employee:
                sex = int(employee['sex'])
            if sex < 0 or sex > 4:
                self.set_status(400)
                self.write({'error': {
                    'code': 'MissingArgument',
                    'message': 'bad sex value'
                }})
                return
        except json.decoder.JSONDecodeError:
            self.set_status(400)
            self.write({'error' : {
                'code': 'BadArguments',
                'message': 'bad body for post'
            }})
            return
        super(EmployeesListHandlerErrorChecking, self).post()


class EmployeeHandler(tornado.web.RequestHandler):
    def get(self, employee_id):
        try:
            emp = model.Employee.select().where(model.Employee.id == employee_id).get()
            self.write(json.dumps(model_to_dict(emp), default=converter))
        except pw.DoesNotExist:
            self.set_status(404)
            self.write('')

    def delete(self, employee_id):
        try:
            emp = model.Employee.select().where(model.Employee.id == employee_id).get()
            emp.delete_instance()
            self.write({'message': employee_id})
        except pw.DoesNotExist:
            self.set_status(404)
            self.write('')
    
    def put(self, employee_id):
        try:
            emp = model.Employee.select().where(model.Employee.id == employee_id).get()
            employee = json.loads(self.request.body)
            emp.name = employee['name']
            emp.sex = employee['sex']
            if not is_date_correct(employee['birthday']):
                self.set_status(500)
                self.write({'error' :{
                    'code': 'BadArguments',
                    'message': 'date should be in YYYY-mm-dd format'
                }})
                return
            emp.birthday = datetime.datetime.strptime(employee['birthday'], '%Y-%m-%d')
            emp.save()
            self.write({'message': employee_id})
        except pw.DoesNotExist:
            self.set_status(404)
            self.write({'error': {
                'code': 'NotFound',
                'message': 'employee with specified ID not found'
            }})

def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/api/employees", EmployeesListHandlerErrorChecking),
        (r"/api/employees/([0-9]+)", EmployeeHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": r"{0}".format(os.path.join(os.path.dirname(__file__), "static"))})
    ],
    debug=True)


if __name__ == "__main__":

    model.proxy.initialize(db)
    db.create_tables([model.Employee])

    app = make_app()
    app.listen(int(os.environ.get('EMPPORT')))
    tornado.ioloop.IOLoop.current().start()
