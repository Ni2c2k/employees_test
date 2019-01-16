import datetime
import peewee as pw
import json

proxy = pw.Proxy()

class BaseModel(pw.Model):
    class Meta:
        database = proxy


class Employee(BaseModel):
    name = pw.CharField()   # just one field for simplicity only
    birthday = pw.DateField(default=datetime.date(2018,1,30))
    sex = pw.IntegerField(default=0) # ISO/IEC 5218
    salary = pw.IntegerField(default=0) # for simplicity
    hiredate = pw.DateField()


def add_employee(emp_dict):
    emp = Employee(name=emp_dict['name'], birthday=datetime.datetime.strptime(emp_dict['birthday'], '%Y-%m-%d'), 
        sex=int(emp_dict['sex']), salary=emp_dict['salary'], hiredate=datetime.datetime.strptime(emp_dict['hiredate'], '%Y-%m-%d'))
    emp.save()
    return emp


class Title(BaseModel):
    title = pw.CharField()
    from_timestamp = pw.DateTimeField(default=datetime.datetime.now)
    employee = pw.ForeignKeyField(Employee, backref='titles', on_delete='CASCADE')


def add_title(title_json, employee):
    title = Title(title=title_json['title'],
        employee=employee)
    title.save()
    return title