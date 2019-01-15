import datetime
import peewee as pw
from playhouse.shortcuts import model_to_dict
import json

proxy = pw.Proxy()

class BaseModel(pw.Model):
    class Meta:
        database = proxy


class Employee(BaseModel):
    name = pw.CharField()
    birthday = pw.DateField(default=datetime.date(2018,1,30))
    sex = pw.IntegerField(default=0) # ISO/IEC 5218


def add_employee(emp_name, emp_birthday, emp_sex):
    emp = Employee(name=emp_name, birthday=emp_birthday, sex=emp_sex)
    emp.save()
    return emp
