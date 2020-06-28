from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, DateTimeField, \
    SelectMultipleField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError,optional

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
    driver = StringField(
        label='驾驶员',
        validators=[DataRequired("驾驶员不能为空")],
        render_kw={"required": False}

    )
    approvaluser = SelectField(
        label='审批人',
        validators=[DataRequired("审批人不能为空")],
        coerce=int,
        choices=[],
        render_kw={"required": False}

    )
    miles = StringField(
        label='部门经理审批意见',
        # validators=[DataRequired("入厂公里数不能为空")],
        render_kw={"required": False},

    )
    outmiles = StringField(
        label='部门经理审批意见',
        # validators=[DataRequired("审批意见不能为空")],
        render_kw={"required": False},

    )
    L1approvereason = StringField(
        label='部门经理审批意见',
        # validators=[DataRequired("审批意见不能为空")],
        render_kw={"required": False},

    )
    L2approvereason = StringField(
        label='综管部经理审批意见',
        # validators=[DataRequired("审批意见不能为空")],
        render_kw={"required": False}

    )
    L3approvereason = StringField(
        label='保安确认出厂',
        # validators=[DataRequired("审批意见不能为空")],
        render_kw={"required": False}

    )
    L4approvereason = StringField(
        label='保安确认入厂',
        # validators=[DataRequired("审批意见不能为空")],
        render_kw={"required": False}

    )
    # procedurelinenode = SelectField(
    #     label='流程节点',
    #     coerce=int,
    #     choices=[],
    #     render_kw={"required": False}
    #
    # )
    submit = SubmitField(
        label="提交申请",

    )


# 快递流程申请表单
class PackageProcedureForm(FlaskForm):

    approvaluser = SelectField(
        label='审批人',
        # validators=[DataRequired("审批人不能为空")],
        coerce=int,
        validators=[optional()],
        choices=[],
        render_kw={"required": False},
        default=0

    )
    logistc_company = SelectField(
        label='物流公司',
        validators=[DataRequired("物流公司不能为空")],
        coerce=int,
        choices=[],
        render_kw={"required": False}

    )

    num = IntegerField(
        label="运单号",
        validators=[DataRequired("运单号不能为空")],
        render_kw={"required": False}

    )
    destination_company = StringField(
        label='对方公司名称',
        validators=[DataRequired("对方公司名称不能为空")],
        render_kw={"required": False}

    )
    package_name = StringField(
        label='快递物品名称',
        validators=[DataRequired("快递物品名称不能为空")],
        render_kw={"required": False}

    )
    payment_method = StringField(
        label='寄/收件方式',
        validators=[DataRequired("寄/收件方式不能为空")],
        render_kw={"required": False}

    )
    collect_person = StringField(
        label='寄/收件人',
        validators=[DataRequired("寄/收件人不能为空")],
        render_kw={"required": False}

    )
    tel = StringField(
        label='联系方式',
        validators=[DataRequired("电话不能为空"), Length(11, 11, "电话必须是11位号码")],
        render_kw={"required": False}

    )
    L3approvereason = StringField(
        label='保安确认出厂',
        # validators=[DataRequired("审批意见不能为空")],
        render_kw={"required": False}

    )
#     # submit = SubmitField(
#     #     label="提交申请",
# )




# 添加新用户
class AddNewUserForm(FlaskForm):
    name = StringField(
        label='姓名',
        validators=[DataRequired("姓名不能为空")],
        render_kw={"required": False}

    )
    department = SelectField(
        label='部门',
        validators=[DataRequired("部门不能为空")],
        coerce=int,
        choices=[],
        render_kw={"required": False}

    )

    tel = StringField(
        label='电话',
        render_kw={"required": False}

    )
    #
    # roleid = IntegerField(
    #     label='角色',
    #     validators=[DataRequired("姓名不能为空")],
    #     render_kw={"required": False}
    #
    # )
    roleid = SelectField(
        label='角色',
        validators=[DataRequired("部门不能为空")],
        coerce=int,
        choices=[],
        render_kw={"required": False}

    )

    submit = SubmitField(
        label="提交申请",

    )


# 修改用户表单
class AlterUserForm(FlaskForm):
    altername = StringField(
        label='姓名',
        validators=[DataRequired("姓名不能为空")],
        render_kw={"required": False}

    )
    alterdepartment = SelectField(
        label='部门',
        validators=[DataRequired("部门不能为空")],
        coerce=int,
        choices=[],
        render_kw={"required": False}

    )

    altertel = StringField(
        label='电话',
        render_kw={"required": False}

    )

    alterroleid = SelectField(
        label='角色',
        validators=[DataRequired("部门不能为空")],
        coerce=int,
        choices=[],
        render_kw={"required": False}

    )
    alterstatus = SelectField(
        label='员工状态',
        validators=[DataRequired("状态不能为空")],
        coerce=int,
        choices=[(0, '删除'), (1, '正常')],
        default=1,
        render_kw={"required": False}

    )

    submit = SubmitField(
        label="提交申请",

    )


# 添加新部门
class AddNewDepartmentForm(FlaskForm):
    newdepartment = StringField(
        label='新的部门名称',
        validators=[DataRequired("部门不能为空")],
        render_kw={"required": False}
    )
    submit = SubmitField(
        label="提交申请",

    )

    # 修改部门表单
class AlterDepartmentForm(FlaskForm):
    alterdepartmentname = StringField(
        label='修改后部门名称',
        validators=[DataRequired("部门不能为空")],
        render_kw={"required": False}
    )
    alterstatus = SelectField(
        label='部门状态',
        validators=[DataRequired("状态不能为空")],
        coerce=int,
        choices=[(0, '删除'), (1, '正常')],
        default=1,
        render_kw={"required": False}

    )

    submit = SubmitField(
    label = "提交申请",

)

#  保安确认入厂公里数
# # class MilesForm(FlaskForm):
#     miles = IntegerField(
#         label='最终公里数',
#         validators=[DataRequired("公里数不能为空")],
#         render_kw={"required": False}
#
#     )
#     procedure_id = StringField(
#         label='最终公里数',
#         # validators=[DataRequired("流程id不能为空")],
#         render_kw={"required": False}
#
#     )
#
#     submit = SubmitField(
#         label="提交申请",
#
#     )
#
#
# # 保安确认出厂公里数
# class OutMilesForm(FlaskForm):
#     outmiles = IntegerField(
#         label='出厂公里数',
#         # validators=[DataRequired("公里数不能为空")],
#         render_kw={"required": False}
#
#     )
#     procedure_id = StringField(
#         label='出厂公里数',
#         # validators=[DataRequired("流程id不能为空")],
#         render_kw={"required": False}
#
#     )
#
#     submit = SubmitField(
#         label="提交申请",
#
#     )
#
#
# # 二级审批拒绝原因
# class L2approvalnok(FlaskForm):
#     rejectreason = StringField(
#         label='拒绝原因',
#         validators=[DataRequired("原因不能为空")],
#         render_kw={"required": False}
#
#     )
#     procedure_id = StringField(
#         label='出厂公里数',
#         # validators=[DataRequired("流程id不能为空")],
#         render_kw={"required": False}
#
#     )
#
#     submit = SubmitField(
#         label="提交申请",
#
#     )
