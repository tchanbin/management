from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateTimeField, \
    SelectMultipleField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from ..models import User


class ResetPwd(FlaskForm):
    old_password = PasswordField(
        label="旧密码",
        validators=[DataRequired(message="旧密码不能为空"), Length(min=6, max=18, message="旧密码6-18位")],
        render_kw={"placeholder": "请输入旧密码",
                   "required": False
                   }

    )

    password1 = PasswordField(
        label="新密码",
        validators=[DataRequired("新密码不能为空"), Length(min=6, max=18, message="新密码6-18位")],
        render_kw={"placeholder": "请输入密码",
                   "required": False
                   }
    )
    password2 = PasswordField(
        label="确认密码",
        validators=[DataRequired("确认密码不能为空"), Length(min=6, max=18, message="新密码6-18位"),
                    EqualTo("password1", message="两次输入密码不一致")],
        render_kw={"placeholder": "确认密码",
                   "required": False}
    )

    submit = SubmitField(
        label="提交",
        render_kw={"class": "btn btn-primary"}
    )

    # @staticmethod
    # def reset_pwd(username, password2):
    #     name = username.data
    #     user = User.query.filter_by(name=name).first()
    #     if user:
    #         User.password = password2.data


class LoginForm(FlaskForm):
    # 登录表单设计
    username = StringField(
        label='姓名',
        validators=[DataRequired("姓名不能为空"), Length(2, 10)],
        render_kw={"placeholder": "请输入姓名", "required": False}
    )

    password = PasswordField(
        label="密码",
        validators=[DataRequired("密码不能为空"), Length(6, 12, message=u"密码应该大于等于6位")],
        render_kw={"placeholder": "请输入密码", "class": "form-control", "required": False}
    )
    remember_me = BooleanField(
        '记住我'
    )
    submit = SubmitField(
        label="登录",
        render_kw={"class": "btn btn-info btn-block"}
    )

    def validate_pwd(self, field):
        if len(field.data) <= 6 or len(field.data) >= 18:
            raise ValidationError("密码不能小于6位，大于18位")


# 用车流程申请表单
class CarProcedureForm(FlaskForm):
    tel = StringField(
        label='联系方式',
        validators=[DataRequired("电话不能为空"), Length(11, 11, "电话必须是11位号码")],
        render_kw={"required": False}

    )
    number = StringField(
        label="乘车人数",

        render_kw={"required": False}

    )
    namelist = StringField(
        label='乘车名单',
        render_kw={"required": False}

    )
    bookstartdatetime = DateTimeField(
        label="预约开始时间",
        validators=[DataRequired("预约日期不能为空")],
        render_kw={"required": False}

    )
    bookenddatetime = DateTimeField(
        label="预约开始时间",
        validators=[DataRequired("预约日期不能为空")],
        render_kw={"required": False}

    )
    arrivalplace = StringField(
        label='目的地',
        validators=[DataRequired("目的地不能为空"), Length(0, 30)],
        render_kw={"required": False}

    )
    reason = StringField(
        label='用车原因',
        validators=[DataRequired("原因不能为空"), Length(0, 100)],
        render_kw={"required": False}

    )
    carname = SelectField(
        label='预约车型',
        validators=[DataRequired("预约车型不能为空")],
        coerce=int,
        choices=[],
        render_kw={"required": False}

    )
    ifetc = BooleanField(
        label='是否需要ETC'
    )

    submit = SubmitField(
        label="提交申请",

    )


class MilesForm(FlaskForm):
    miles = IntegerField(
        label='最终公里数',
        # validators=[DataRequired("公里数不能为空")],
        render_kw={"required": False}

    )
    procedure_id = StringField(
        label='最终公里数',
        # validators=[DataRequired("流程id不能为空")],
        render_kw={"required": False}

    )

    submit = SubmitField(
        label="提交申请",

    )

# 添加新用户
class AddNewUser(FlaskForm):
    name = StringField(
        label='姓名',
        validators=[DataRequired("姓名不能为空")],
        render_kw={"required": False}

    )

    tel= StringField(
        label='电话',
        render_kw={"required": False}

    )

    roleid = IntegerField(
        label='角色',
        validators=[DataRequired("姓名不能为空")],
        render_kw={"required": False}

    )

    submit = SubmitField(
        label="提交申请",

    )
