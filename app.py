import tornado.ioloop
import tornado.web
import json
import os
import model as model
import peewee as pw
from playhouse.shortcuts import model_to_dict
import playhouse.db_url
import datetime

# db = playhouse.db_url.connect(os.environ.get('EMPDATABASE'))
db = pw.SqliteDatabase('sqlite.db', pragmas={
    'foreign_keys': 1
})

def converter(obj):
    if isinstance(obj, datetime.date):
        return obj.__str__()


def is_date_correct(date):
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
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
            'sex': emp.sex,
            'salary': emp.salary})
        self.write({'employees': emps_data})

    def post(self):
        emp = model.add_employee(json.loads(self.request.body))
        self.set_status(201)
        self.write({'Location': 'http://localhost:8888/api/employees/{0}'.format(emp.id)})


class EmployeesListHandlerErrorChecking(EmployeesListHandler):
    def get(self):
        super(EmployeesListHandlerErrorChecking, self).get()
    
    def post(self):
        try:
            employee = json.loads(self.request.body)

            for param in ['name', 'birthday', 'sex', 'salary', 'hiredate']:
                if param not in employee:
                    self.set_status(400)
                    self.write({
                        'error': {
                            'code': 'MissingArgument',
                            'message': '{0} should be specified'.format(param)
                        }
                    })
                    return
            
            if not is_date_correct(employee['birthday']) or not is_date_correct(employee['hiredate']):
                self.set_status(400)
                self.write({'error' :{
                    'code': 'BadArguments',
                    'message': 'date should be in YYYY-mm-dd format'
                }})
                return
            
            sex = int(employee['sex'])
            if sex < 0 or sex > 4:
                self.set_status(400)
                self.write({'error': {
                    'code': 'BadArguments',
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
            emp.hiredate = datetime.datetime.strptime(employee['hiredate'], '%Y-%m-%d')
            emp.salary = employee['salary']
            emp.save()
            self.write({'message': employee_id})
        except pw.DoesNotExist:
            self.set_status(404)
            self.write({'error': {
                'code': 'NotFound',
                'message': 'employee with specified ID not found'
            }})


class TitleListHandler(tornado.web.RequestHandler):
    def get(self, employee_id):
        query = model.Title.select().join(model.Employee).where(model.Employee.id == employee_id)
        titles = []
        for title in query:
            titles.append({'id': title.id,
            'title': title.title,
            'from_timestamp': title.from_timestamp.__str__()})
        self.write({'titles': titles})
    def post(self, employee_id):
        emp = model.Employee.select().where(model.Employee.id == employee_id).get()
        title = model.add_title(json.loads(self.request.body), emp)
        self.set_status(201)
        self.write({'emp': employee_id, 'title_id': title.id})


def make_app():
    return tornado.web.Application([
        (r"/", MainHandler),
        (r"/api/employees", EmployeesListHandlerErrorChecking),
        (r"/api/employees/([0-9]+)/titles", TitleListHandler),
        (r"/api/employees/([0-9]+)", EmployeeHandler),
        (r"/(.*)", tornado.web.StaticFileHandler, {"path": r"{0}".format(os.path.join(os.path.dirname(__file__), "static"))})
    ],
    debug=True)


if __name__ == "__main__":

    model.proxy.initialize(db)
    db.create_tables([model.Employee, model.Title])

    app = make_app()
    app.listen(int(os.environ.get('EMPPORT')))
    tornado.ioloop.IOLoop.current().start()
