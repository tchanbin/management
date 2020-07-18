from flask import render_template, redirect, url_for, abort, flash, request, \
    current_app, make_response, g, session, Response, jsonify, json, Markup
from .forms import LoginForm, ResetPwd, CarProcedureForm, AddNewUserForm, PackageProcedureForm, \
    AlterUserForm, AlterDepartmentForm, AddNewDepartmentForm
from flask_login import login_required, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_, extract, func
from ..models import Permission, Role, User, CarProcedureInfo, CarList, ProcedureList, PackageProcedureInfo, \
    CompanyDepartment, times, ProcedureApproval, ProcedureLine, ProcedureNode, ProcedureState, FieldPermission, \
    LogisticCompanyList, Order, House
from . import home
from management import db, excel
from datetime import datetime
from management.decorators import permission_required
from openpyxl import Workbook
from openpyxl.writer.excel import save_virtual_workbook
import uuid


# 用户登录
@home.route("/", methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and user.verify_password(form.password.data) and user.status == "正常":
            login_user(user, form.remember_me.data)
            next = request.args.get("next")
            if next is None or not next.startswith("/"):
                next = url_for("home.todolist")
            return redirect(next)
        flash("用户名或者密码错误")
    return render_template('home/login.html', form=form)


# 我的待办流程
@home.route("/todolist", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def todolist():
    page = request.args.get("page", 1, type=int)
    # 角色为管理员的可以看见所有运行中的流程信息
    if current_user.role_id == 5:
        pagination = ProcedureApproval.query.join(User,
                                                  ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
            User).filter(
            ProcedureApproval.procedure_approval_state == 1,
            ProcedureApproval.procedure_approval_company == current_user.company,
        ).order_by(
            ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        daibanno = ProcedureApproval.query.filter(
            ProcedureApproval.procedure_approval_state == 1,
            ProcedureApproval.procedure_approval_company == current_user.company, ).count()
        session["daibanno"] = daibanno
    #     保安可以看见自己相关的信息
    elif current_user.role_id == 2:
        pagination = ProcedureApproval.query.join(User,
                                                  ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
            User).filter(
            ProcedureApproval.procedure_approval_current_line_node_id.in_(["4", "5"]),
            ProcedureApproval.procedure_approval_company == current_user.company,
            ProcedureApproval.procedure_approval_state == 1,
        ).order_by(
            ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        daibanno = ProcedureApproval.query.filter(
            ProcedureApproval.procedure_approval_current_line_node_id.in_(["4", "5"]),
            ProcedureApproval.procedure_approval_state == 1,
            ProcedureApproval.procedure_approval_company == current_user.company, ).count()
        session["daibanno"] = daibanno
    #     普通用户和经理可以看见自己的待办信息
    else:
        pagination = ProcedureApproval.query.join(User,
                                                  ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
            User).filter(
            ProcedureApproval.procedure_approval_user_id == current_user.id,
            ProcedureApproval.procedure_approval_company == current_user.company,

            ProcedureApproval.procedure_approval_state.in_(["0", "1"]),
        ).order_by(
            ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        daibanno = ProcedureApproval.query.filter(
            ProcedureApproval.procedure_approval_user_id == current_user.id,
            ProcedureApproval.procedure_approval_company == current_user.company,
            ProcedureApproval.procedure_approval_state == 1).count()
        session["daibanno"] = daibanno
    my_procedure = pagination.items

    return render_template("home/todolist.html", my_procedure=my_procedure, pagination=pagination)


# # 我的发起的所有的流程
# @home.route("/myprocedures", methods=["GET", "POST"]) 保存备份用
# @login_required
# def myprocedures():
#     page = request.args.get("page", 1, type=int)
#     procedurename = request.args.get("procedurename", "")
#     procedurestate = request.args.get("procedurestate", "")
#     proceduredate = request.args.get("proceduredate", "")
#     # 角色为管理员的可以看见所有运行中的流程信息
#     if current_user.role_id == 5:
#
#         pagination = ProcedureApproval.query.join(User,
#                                                   ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
#             User).join(ProcedureState,
#                        ProcedureApproval.procedure_approval_flowid == ProcedureState.procedure_state_flowid).add_entity(
#             ProcedureState).filter(
#
#             ProcedureApproval.procedure_approval_current_line_node_id == 1,
#             ProcedureApproval.procedure_approval_company == current_user.company,
#             ProcedureApproval.procedure_approval_flowname.contains(procedurename),
#             ProcedureApproval.procedure_approval_approval_datetime.contains(proceduredate),
#             ProcedureState.procedure_state.contains(procedurestate),
#
#         ).with_entities(
#
#             ProcedureApproval.procedure_approval_flowid,
#             ProcedureApproval.procedure_approval_flowname,
#             ProcedureState.procedure_state,
#             func.max(ProcedureApproval.procedure_approval_approval_datetime).label("approval_datetime"),
#             ProcedureApproval.procedure_approval_flowmodal,
#         ).group_by(ProcedureApproval.procedure_approval_flowid).order_by(
#             ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
#         ["FLASKY_PER_PAGE"], error_out=False)
#     else:
#         pagination = ProcedureApproval.query.join(User,
#                                                   ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
#             User).join(ProcedureState,
#                        ProcedureApproval.procedure_approval_flowid == ProcedureState.procedure_state_flowid).add_entity(
#             ProcedureState).filter(
#             ProcedureApproval.procedure_approval_user_id == current_user.id,
#             ProcedureApproval.procedure_approval_company == current_user.company,
#             ProcedureApproval.procedure_approval_current_line_node_id == 1,
#             ProcedureApproval.procedure_approval_flowname.contains(procedurename),
#             ProcedureApproval.procedure_approval_approval_datetime.contains(proceduredate),
#             ProcedureState.procedure_state.contains(procedurestate),
#
#         ).with_entities(
#
#             ProcedureApproval.procedure_approval_flowid,
#             ProcedureApproval.procedure_approval_flowname,
#             ProcedureState.procedure_state,
#             func.max(ProcedureApproval.procedure_approval_approval_datetime).label("approval_datetime"),
#             ProcedureApproval.procedure_approval_flowmodal,
#         ).group_by(ProcedureApproval.procedure_approval_flowid).order_by(
#             ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
#         ["FLASKY_PER_PAGE"], error_out=False)
#
#     my_procedure = pagination.items
#
#     return render_template("home/myprocedures.html", my_procedure=my_procedure, pagination=pagination,
#                            procedurename=procedurename,
#                            procedurestate=procedurestate, proceduredate=proceduredate)

# 我的发起的所有的流程
@home.route("/myprocedures", methods=["GET", "POST"])
@login_required
def myprocedures():
    page = request.args.get("page", 1, type=int)
    procedurename = request.args.get("procedurename", "")
    procedurestate = request.args.get("procedurestate", "")
    proceduredate = request.args.get("proceduredate", "")
    # 角色为管理员的可以看见所有运行中的流程信息
    if current_user.role_id == 5:

        pagination = ProcedureState.query.join(User,
                                               ProcedureState.procedure_state_user_id == User.id).add_entity(
            User).filter(

            ProcedureState.procedure_state == 1,
            User.company == current_user.company,
            ProcedureState.procedure_state_name.contains(procedurename),
            ProcedureState.procedure_state_approval_datetime.contains(proceduredate),
            ProcedureState.procedure_state.contains(procedurestate),

        ).with_entities(

            ProcedureState.procedure_state_name,
            ProcedureState.procedure_state,
            ProcedureState.procedure_state_approval_datetime,
            User.username,
            ProcedureState.procedure_state_flowmodal,
            ProcedureState.procedure_state_flowid,
        ).distinct().order_by(
            ProcedureState.procedure_state_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
    else:
        pagination = ProcedureState.query.join(User,
                                               ProcedureState.procedure_state_user_id == User.id).add_entity(
            User).filter(
            ProcedureState.procedure_state_user_id == current_user.id,

            ProcedureState.procedure_state_name.contains(procedurename),
            ProcedureState.procedure_state_approval_datetime.contains(proceduredate),
            ProcedureState.procedure_state.contains(procedurestate),

        ).with_entities(

            ProcedureState.procedure_state_flowid,
            ProcedureState.procedure_state_approval_datetime,
            ProcedureState.procedure_state_name,
            ProcedureState.procedure_state,
            ProcedureState.procedure_state_flowmodal,
        ).distinct().order_by(
            ProcedureState.procedure_state_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)

    my_procedure = pagination.items

    return render_template("home/myprocedures.html", my_procedure=my_procedure, pagination=pagination,
                           procedurename=procedurename,
                           procedurestate=procedurestate, proceduredate=proceduredate)


# # 我的所有已办流程（不是发起，而是经过审批的流程）保存备份用
# @home.route("/doneprocedures", methods=["GET", "POST"])
# @login_required
# def doneprocedures():
#     page = request.args.get("page", 1, type=int)
#     procedurename = request.args.get("procedurename", "")
#     procedurestate = request.args.get("procedurestate", "")
#     proceduredate = request.args.get("proceduredate", "")
#     # 找到所有审批人的流程的32位ID，形成列表
#     procedures2 = db.session.query(ProcedureApproval.procedure_approval_flowid).filter(
#         ProcedureApproval.procedure_approval_user_id == current_user.id,
#         ProcedureApproval.procedure_approval_current_line_node_id != 1,
#         ProcedureApproval.procedure_approval_state == 2,
#     ).distinct()
#     list = [c.procedure_approval_flowid for c in procedures2]
#     # 在流程状态中按照列表进行查询
#     pagination = ProcedureState.query.join(User,
#                                            ProcedureState.procedure_state_user_id == User.id).add_entity(
#         User).join(ProcedureApproval,
#                    ProcedureState.procedure_state_flowid == ProcedureApproval.procedure_approval_flowid).add_entity(
#         ProcedureApproval).filter(
#         ProcedureState.procedure_state_flowid.in_(list),
#
#         ProcedureApproval.procedure_approval_current_line_node_id == 1,
#         ProcedureApproval.procedure_approval_flowname.contains(procedurename),
#         ProcedureApproval.procedure_approval_approval_datetime.contains(proceduredate),
#         ProcedureState.procedure_state.contains(procedurestate),
#
#     ).with_entities(
#
#         ProcedureState.procedure_state_name,
#         ProcedureState.procedure_state,
#         User.username,
#         func.max(ProcedureApproval.procedure_approval_approval_datetime).label("approval_datetime"),
#         ProcedureState.procedure_state_flowmodal,
#         ProcedureState.procedure_state_flowid,
#     ).group_by(ProcedureApproval.procedure_approval_flowid).order_by(
#         ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
#     ["FLASKY_PER_PAGE"], error_out=False)
#
#     my_procedure = pagination.items
#
#     return render_template("home/doneprocedures.html", my_procedure=my_procedure, pagination=pagination,
#                            procedurename=procedurename,
#                            procedurestate=procedurestate, proceduredate=proceduredate)


# 我的所有已办流程（不是发起，而是经过审批的流程）保存备份用
@home.route("/doneprocedures", methods=["GET", "POST"])
@login_required
def doneprocedures():
    page = request.args.get("page", 1, type=int)
    procedurename = request.args.get("procedurename", "")
    procedurestate = request.args.get("procedurestate", "")
    proceduredate = request.args.get("proceduredate", "")
    # 找到所有审批人的流程的32位ID，形成列表
    procedures2 = db.session.query(ProcedureApproval.procedure_approval_flowid).filter(
        ProcedureApproval.procedure_approval_user_id == current_user.id,
        ProcedureApproval.procedure_approval_current_line_node_id != 1,
        ProcedureApproval.procedure_approval_state == 2,
    ).distinct()
    list = [c.procedure_approval_flowid for c in procedures2]
    # 在流程状态中按照列表进行查询
    pagination = ProcedureState.query.join(User,
                                           ProcedureState.procedure_state_user_id == User.id).add_entity(
        User).filter(
        ProcedureState.procedure_state_flowid.in_(list),
        User.company == current_user.company,
        ProcedureState.procedure_state_name.contains(procedurename),
        ProcedureState.procedure_state_approval_datetime.contains(proceduredate),
        ProcedureState.procedure_state.contains(procedurestate),

    ).with_entities(

        ProcedureState.procedure_state_name,
        ProcedureState.procedure_state,
        ProcedureState.procedure_state_approval_datetime,
        User.username,
        ProcedureState.procedure_state_flowmodal,
        ProcedureState.procedure_state_flowid,
    ).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)

    my_procedure = pagination.items

    return render_template("home/doneprocedures.html", my_procedure=my_procedure, pagination=pagination,
                           procedurename=procedurename,
                           procedurestate=procedurestate, proceduredate=proceduredate)


# 快递流程主页
@home.route("/packageindex", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def packageindex():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")

    pagination = PackageProcedureInfo.query.filter(PackageProcedureInfo.collect_person == current_user.username,
                                                   PackageProcedureInfo.approval_time.contains(keywords),

                                                   ).order_by(
        PackageProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    my_procedure = pagination.items

    return render_template("home/packageindex.html", my_procedure=my_procedure, pagination=pagination)


# 发起流程申请页面
@home.route("/startapproval", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def startapproval():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")
    pagination = ProcedureList.query.filter(
        ProcedureList.procedure_list_name.contains(keywords),
    ).order_by(
        ProcedureList.procedure_list_id.asc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    procedure_lists = pagination.items

    return render_template("home/startapproval.html", procedure_lists=procedure_lists, pagination=pagination)


# 公务用车流程申请表
@home.route("/procedureapproval1", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def procedureapproval1():
    # 生成公务用车流程申请表单对象
    form = CarProcedureForm()
    # 给车名字的下拉列表找到车型
    form.carname.choices = [(c.id, c.name) for c in CarList.query.filter_by(company=current_user.company)]
    # 给审批经理的下拉列表找到审批人
    form.approvaluser.choices = [(c.id, c.username) for c in
                                 User.query.filter(User.company == current_user.company,
                                                   User.departmentid == current_user.departmentid,
                                                   User.role_id.in_(["3", "4", "5"]))]
    # 查找到所有二级审批通过的车的申请信息
    carusestatus = CarProcedureInfo.query.filter(
        CarProcedureInfo.state.in_(["2", "3"], )
    ).order_by(CarProcedureInfo.book_start_datetime.desc()).all()
    # 对表单的提交内容进行验证
    if form.validate_on_submit():
        flowid = str(uuid.uuid1())
        car_procedure_approval = CarProcedureInfo(id=flowid,
                                                  procedure_list_id=1,
                                                  procedure_list_flowmodal="carprocedure",
                                                  user_id=current_user.id,
                                                  departmentid=current_user.departmentid,
                                                  tel=form.tel.data,
                                                  car_id=form.carname.data,
                                                  book_start_datetime=form.bookstartdatetime.data,
                                                  book_end_datetime=form.bookenddatetime.data,
                                                  number=form.number.data,
                                                  namelist=form.namelist.data,
                                                  arrival_place=form.arrivalplace.data,
                                                  etc=form.ifetc.data,
                                                  company=current_user.company,
                                                  driver=form.driver.data,
                                                  reason=form.reason.data,
                                                  current_line_node_id=2,
                                                  state=1

                                                  )
        car = CarList.query.filter_by(id=form.carname.data).first()

        procedure_approval1 = ProcedureApproval(procedure_approval_flowid=flowid,
                                                procedure_approval_flowname=current_user.username + "的" + car.name + "用车流程申请",
                                                procedure_approval_current_line_node_id=1,
                                                procedure_approval_user_id=current_user.id,
                                                procedure_approval_flowmodal="carproceduremodal",
                                                procedure_approval_approval_datetime=datetime.now(),
                                                procedure_approval_state=2,
                                                procedure_approval_company=current_user.company
                                                )
        procedure_approval = ProcedureApproval(procedure_approval_flowid=flowid,
                                               procedure_approval_flowname=current_user.username + "的" + car.name + "用车流程申请",
                                               procedure_approval_current_line_node_id=2,
                                               procedure_approval_user_id=form.approvaluser.data,
                                               procedure_approval_flowmodal="carproceduremodal",
                                               procedure_approval_approval_datetime=datetime.now(),
                                               procedure_approval_state=1,
                                               procedure_approval_company=current_user.company
                                               )
        procedure_state = ProcedureState(
            procedure_state_flowid=flowid,
            procedure_state_name=current_user.username + "的" + car.name + "用车流程申请",
            procedure_state=1,
            procedure_state_flowmodal="carproceduremodal",
            procedure_state_procedure_list_name="公务用车申请表",
            procedure_state_user_id=current_user.id,
            procedure_state_approval_datetime=datetime.now()

        )

        db.session.add(car_procedure_approval)
        db.session.add(procedure_approval1)
        db.session.add(procedure_approval)
        db.session.add(procedure_state)
        try:
            db.session.commit()
            flash("您的用车申请已经提交成功，请到我的流程查看")
            return redirect(url_for("home.myprocedures"))
        except:
            db.session.rollback()
            flash("提交数据失败")
            abort(404)
    return render_template("home/procedureapproval1.html", current_time=datetime.utcnow(), form=form,
                           carusestatus=carusestatus)


# 公务用车申请模板
@home.route("/carproceduremodal", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def carproceduremodal():
    # 进入流程申请的模板
    if request.method == "GET":
        # 生成公务用车流程申请表单对象
        form = CarProcedureForm()
        # 获取请求的流程ID和入口参数
        procedure_id = request.args.get("procedure_id")
        procedure_door = request.args.get("procedure_door")
        # 生成用车下拉列表
        form.carname.choices = [(c.id, c.name) for c in CarList.query.filter_by(company=current_user.company)]

        # 查询该条用车申请的用车信息和审批信息
        myprocedure = CarProcedureInfo.query.join(ProcedureApproval,
                                                  CarProcedureInfo.id == ProcedureApproval.procedure_approval_flowid).add_entity(
            ProcedureApproval).join(User, CarProcedureInfo.user_id == User.id).add_entity(
            User).filter(CarProcedureInfo.id == procedure_id).first()
        rejectnodes = [(c.procedure_line_next_line_id, c.procedure_line_description) for c in
                       ProcedureLine.query.filter(
                           ProcedureLine.procedure_line_flowmodal == myprocedure.ProcedureApproval.procedure_approval_flowmodal,
                           ProcedureLine.procedure_line_pre_line_id == myprocedure.CarProcedureInfo.current_line_node_id,
                           ProcedureLine.procedure_line_next_line_id < myprocedure.CarProcedureInfo.current_line_node_id)]
        # 获得当前该条流程的节点值
        if myprocedure:
            # 通过入门的只读属性判断是否是只读，指定了第6个专属设置只读的节点，因为是通过节点控制权限。
            if procedure_door == "read":
                current_node = 6
            else:
                current_node = myprocedure.CarProcedureInfo.current_line_node_id
            form.carname.data = myprocedure.CarProcedureInfo.car_id
            form.bookstartdatetime.data = myprocedure.CarProcedureInfo.book_start_datetime
            form.bookenddatetime.data = myprocedure.CarProcedureInfo.book_end_datetime
            form.arrivalplace.data = myprocedure.CarProcedureInfo.arrival_place
            form.namelist.data = myprocedure.CarProcedureInfo.namelist
            form.number.data = myprocedure.CarProcedureInfo.number
            form.reason.data = myprocedure.CarProcedureInfo.reason
            form.ifetc.data = myprocedure.CarProcedureInfo.etc
            form.driver.data = myprocedure.CarProcedureInfo.driver
            if current_node == 1:
                form.approvaluser.choices = [(c.id, c.username) for c in
                                             User.query.filter(User.company == current_user.company,
                                                               User.departmentid == current_user.departmentid,
                                                               User.role_id.in_(["3", "4"]))]
            elif current_node == 2:
                form.approvaluser.choices = [(c.id, c.username) for c in
                                             User.query.filter(User.company == current_user.company,

                                                               User.role_id.in_(["4"]))]
            else:
                form.approvaluser.choices = [(c.id, c.username) for c in
                                             User.query.filter(User.company == current_user.company,
                                                               User.role_id.in_(["2"]))]

            form.approvaluser.data = myprocedure.ProcedureApproval.procedure_approval_user_id
            L1approvalreasons = ProcedureApproval.query.join(User,
                                                             ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
                User).filter(ProcedureApproval.procedure_approval_flowid == procedure_id,
                             ProcedureApproval.procedure_approval_state == 2,
                             ProcedureApproval.procedure_approval_current_line_node_id == 2
                             )
            L2approvalreasons = ProcedureApproval.query.join(User,
                                                             ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
                User).filter(ProcedureApproval.procedure_approval_flowid == procedure_id,
                             ProcedureApproval.procedure_approval_state == 2,
                             ProcedureApproval.procedure_approval_current_line_node_id == 3
                             )
            L3approvalreasons = ProcedureApproval.query.join(User,
                                                             ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
                User).join(CarProcedureInfo,
                           ProcedureApproval.procedure_approval_flowid == CarProcedureInfo.id).add_entity(
                CarProcedureInfo).filter(ProcedureApproval.procedure_approval_flowid == procedure_id,
                                         ProcedureApproval.procedure_approval_state == 2,
                                         ProcedureApproval.procedure_approval_current_line_node_id == 4
                                         )
            L4approvalreasons = ProcedureApproval.query.join(User,
                                                             ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
                User).join(CarProcedureInfo,
                           ProcedureApproval.procedure_approval_flowid == CarProcedureInfo.id).add_entity(
                CarProcedureInfo).filter(ProcedureApproval.procedure_approval_flowid == procedure_id,
                                         ProcedureApproval.procedure_approval_state == 2,
                                         ProcedureApproval.procedure_approval_current_line_node_id == 5
                                         )

            filedpermissions = FieldPermission.query.filter(
                FieldPermission.field_permission_node == current_node,
                FieldPermission.field_permission_flowmodal == "carprocedure").all()
            for filedpermission in filedpermissions:
                if filedpermission.field_permission_read == "1":
                    # 获取字段权限表的字段名称
                    filedname = filedpermission.field_permission_field_name
                    # 找到Form中该字段对应的属性，并修改赋值其属性为不可用。
                    getattr(form, filedname).render_kw = {"disabled": "disabled"}

            return render_template("home/carproceduremodal.html", current_time=datetime.utcnow(), form=form,
                                   myprocedure=myprocedure, L1approvalreasons=L1approvalreasons,
                                   L2approvalreasons=L2approvalreasons, L3approvalreasons=L3approvalreasons,
                                   L4approvalreasons=L4approvalreasons, current_node=current_node,
                                   procedure_door=procedure_door, rejectnodes=rejectnodes)
    # 提交用车流程申请
    if request.method == "POST":
        procedure_id = request.args.get("procedure_id")
        if procedure_id:
            car_procedure_info = CarProcedureInfo.query.filter_by(id=procedure_id).first()
            node = car_procedure_info.current_line_node_id
        procedure_door = request.args.get("procedure_door")
        form = CarProcedureForm()
        # 进入部门经理审批环节
        # 判断是否是驳回
        if request.values.get("sbbtn") == "reject":
            rejectnode = request.form.get("rejectnode")
            reject_procedure_id = request.form.get("reject_procedure_id")
            rejectreason = request.form.get("rejectreason")
            current_node_id = request.form.get("current_node_id")
            # 拿到用车信息表并修改节点为驳回节点
            car_procedure_info = CarProcedureInfo.query.filter_by(id=reject_procedure_id).first()
            current_node_id = car_procedure_info.current_line_node_id
            car_procedure_info.current_line_node_id = rejectnode
            # 查找当前的审批节点,变更他的状态从1到2
            reject_procedure_close = ProcedureApproval.query.filter(
                ProcedureApproval.procedure_approval_flowid == reject_procedure_id,
                ProcedureApproval.procedure_approval_current_line_node_id == current_node_id,
                ProcedureApproval.procedure_approval_state == 1,
            ).first()

            reject_procedure_close.procedure_approval_state = 2
            reject_procedure_close.procedure_approval_reason = rejectreason
            reject_procedure_close.procedure_approval_user_id = current_user.id
            # 找到应该驳回的节点的那条审批记录，并找到该条记录的审批人。
            reject_procedure_close_pre = ProcedureApproval.query.filter(
                ProcedureApproval.procedure_approval_flowid == reject_procedure_id,
                ProcedureApproval.procedure_approval_current_line_node_id == rejectnode,
            ).first()

            rejectuserid = reject_procedure_close_pre.procedure_approval_user_id
            # 拼接用户姓名
            approval_name = car_procedure_info.users.username
            carnamepinjie = car_procedure_info.cars.name

            # 在审批表中新增驳回节点
            reject_approval = ProcedureApproval(procedure_approval_flowid=reject_procedure_id,
                                                procedure_approval_flowname=approval_name + "的" + carnamepinjie + "用车流程申请",
                                                procedure_approval_current_line_node_id=rejectnode,
                                                procedure_approval_user_id=rejectuserid,

                                                procedure_approval_flowmodal="carproceduremodal",
                                                procedure_approval_approval_datetime=datetime.now(),
                                                procedure_approval_state=1,
                                                procedure_approval_company=current_user.company
                                                )

            db.session.add(reject_approval)
            db.session.add(reject_procedure_close)
            db.session.add(reject_procedure_close_pre)

            try:
                db.session.commit()
                flash("您的用车申请已经驳回成功")
                return redirect(url_for("home.todolist"))
            except:
                db.session.rollback()
                flash("提交数据失败")
                abort(404)
            return redirect(url_for("home.todolist"))
        #     如果不是驳回正常进行审批，节点为1就是要进行驳回后的提交
        # 如果是点击了取消按钮，则进入以下流程。
        if request.values.get("sbbtn") == "cancel":
            if request.values.get("sbbtn") == "cancel":

                cancel_procedure_id = request.form.get("cancel_procedure_id")
                cancelreason = request.form.get("cancelreason")

                # 拿到用车信息表并修改节点为取消状态
                car_procedure_info = CarProcedureInfo.query.filter_by(id=cancel_procedure_id).first()
                current_node_id = car_procedure_info.current_line_node_id
                car_procedure_info.state = 5
                # 查找当前的审批节点,变更他的状态从1到2
                cancel_procedure_close = ProcedureApproval.query.filter(
                    ProcedureApproval.procedure_approval_flowid == cancel_procedure_id,
                    ProcedureApproval.procedure_approval_current_line_node_id == current_node_id,
                    ProcedureApproval.procedure_approval_state == 1,
                ).first()

                cancel_procedure_close.procedure_approval_state = 2
                cancel_procedure_close.procedure_approval_reason = cancelreason
                cancel_procedure_close.procedure_approval_user_id = current_user.id
                #     去流程状态表里修改运行中的状态为完成
                proedure_state = ProcedureState.query.filter_by(procedure_state_flowid=cancel_procedure_id).first()
                proedure_state.procedure_state = 5
                # 体积修改对象
                db.session.add(proedure_state)
                db.session.add(car_procedure_info)
                db.session.add(cancel_procedure_close)

                try:
                    db.session.commit()
                    flash("您的用车申请已经取消成功")
                    return redirect(url_for("home.todolist"))
                except:
                    db.session.rollback()
                    flash("提交数据失败")
                    abort(404)
                return redirect(url_for("home.todolist"))
        if node == 1 and current_user.can(Permission.APPLY):
            # 修改审批表的state从1变更为2
            alter_approval_state = ProcedureApproval.query.filter_by(procedure_approval_flowid=procedure_id,
                                                                     procedure_approval_current_line_node_id=1,
                                                                     procedure_approval_state=1,
                                                                     ).first()

            alter_approval_state.procedure_approval_state = 2
            alter_approval_state.procedure_approval_user_id = current_user.id
            alter_approval_state.procedure_approval_approval_datetime = datetime.now()

            # 启动下一审批节点，新增， 对用车审批表里的用车节点插入为2（部门经理审批），state设置为1
            #  对流程进行流程名字拼接
            approval_name = car_procedure_info.users.username
            carnamepinjie = car_procedure_info.cars.name

            procedure_approval = ProcedureApproval(procedure_approval_flowid=procedure_id,
                                                   procedure_approval_flowname=approval_name + "的" + carnamepinjie + "用车流程申请",
                                                   procedure_approval_current_line_node_id=2,
                                                   procedure_approval_user_id=form.approvaluser.data,
                                                   # procedure_approval_reason=form.L1approvereason.data,
                                                   procedure_approval_flowmodal="carproceduremodal",
                                                   procedure_approval_approval_datetime=datetime.now(),
                                                   procedure_approval_state=1,
                                                   procedure_approval_company=current_user.company
                                                   )
            # 对用车流程信息表里的信息进行更新
            car_procedure_info.car_id = form.carname.data
            car_procedure_info.book_start_datetime = form.bookstartdatetime.data
            car_procedure_info.book_end_datetime = form.bookenddatetime.data
            car_procedure_info.arrival_place = form.arrivalplace.data
            car_procedure_info.namelist = form.namelist.data
            car_procedure_info.number = form.number.data
            car_procedure_info.reason = form.reason.data
            car_procedure_info.etc = form.ifetc.data
            car_procedure_info.driver = form.driver.data

            # 修改用车信息表的状态和节点
            car_procedure_info.state = 1
            car_procedure_info.current_line_node_id = 2

        if node == 2 and current_user.can(Permission.L1_APPROVAL):

            # 修改审批表的state从1变更为2
            alter_approval_state = ProcedureApproval.query.filter_by(procedure_approval_flowid=procedure_id,
                                                                     procedure_approval_current_line_node_id=2,
                                                                     procedure_approval_state=1,
                                                                     ).first()

            alter_approval_state.procedure_approval_state = 2
            alter_approval_state.procedure_approval_user_id = current_user.id
            alter_approval_state.procedure_approval_approval_datetime = datetime.now()
            if form.L1approvereason.data:
                alter_approval_state.procedure_approval_reason = form.L1approvereason.data
            alter_approval_state.procedure_approval_approval_datetime = datetime.now()

            # 启动下一审批节点，新增， 对用车审批表里的用车节点插入为3（综管部经理审批），state设置为1
            #  对流程进行流程名字拼接
            approval_name = car_procedure_info.users.username
            carnamepinjie = car_procedure_info.cars.name

            procedure_approval = ProcedureApproval(procedure_approval_flowid=procedure_id,
                                                   procedure_approval_flowname=approval_name + "的" + carnamepinjie + "用车流程申请",
                                                   procedure_approval_current_line_node_id=3,
                                                   procedure_approval_user_id=form.approvaluser.data,
                                                   # procedure_approval_reason=form.L1approvereason.data,
                                                   procedure_approval_flowmodal="carproceduremodal",
                                                   procedure_approval_approval_datetime=datetime.now(),
                                                   procedure_approval_state=1,
                                                   procedure_approval_company=current_user.company
                                                   )
            # 对用车流程信息表里的信息进行更新
            car_procedure_info.car_id = form.carname.data
            car_procedure_info.book_start_datetime = form.bookstartdatetime.data
            car_procedure_info.book_end_datetime = form.bookenddatetime.data
            car_procedure_info.arrival_place = form.arrivalplace.data
            car_procedure_info.namelist = form.namelist.data
            car_procedure_info.number = form.number.data
            car_procedure_info.reason = form.reason.data
            car_procedure_info.etc = form.ifetc.data
            car_procedure_info.driver = form.driver.data

            # 修改用车信息表的状态和节点
            car_procedure_info.state = 1
            car_procedure_info.current_line_node_id = 3
        # 进入综管部经理审批环节
        elif node == 3 and current_user.can(Permission.L2_APPROVAL):
            # 修改审批表的state从1变更为2
            alter_approval_state = ProcedureApproval.query.filter_by(procedure_approval_flowid=procedure_id,
                                                                     procedure_approval_current_line_node_id=3,
                                                                     procedure_approval_state=1, ).first()
            alter_approval_state.procedure_approval_state = 2
            alter_approval_state.procedure_approval_user_id = current_user.id
            alter_approval_state.procedure_approval_approval_datetime = datetime.now()
            if form.L2approvereason.data:
                alter_approval_state.procedure_approval_reason = form.L2approvereason.data
            alter_approval_state.procedure_approval_approval_datetime = datetime.now()

            # 新增， 对用车审批表里的用车节点插入为4（保安出厂），state设置为1
            #  对流程进行流程名字拼接
            approval_name = car_procedure_info.users.username
            carnamepinjie = car_procedure_info.cars.name
            procedure_approval = ProcedureApproval(procedure_approval_flowid=procedure_id,
                                                   procedure_approval_flowname=approval_name + "的" + carnamepinjie + "用车流程申请",
                                                   procedure_approval_current_line_node_id=4,
                                                   procedure_approval_user_id=form.approvaluser.data,
                                                   # procedure_approval_reason=form.L2approvereason.data,
                                                   procedure_approval_flowmodal="carproceduremodal",
                                                   procedure_approval_approval_datetime=datetime.now(),
                                                   procedure_approval_state=1,
                                                   procedure_approval_company=current_user.company
                                                   )
            # 对用车流程信息表里的信息进行更新
            car_procedure_info.car_id = form.carname.data
            car_procedure_info.book_start_datetime = form.bookstartdatetime.data
            car_procedure_info.book_end_datetime = form.bookenddatetime.data
            car_procedure_info.arrival_place = form.arrivalplace.data
            car_procedure_info.namelist = form.namelist.data
            car_procedure_info.number = form.number.data
            car_procedure_info.reason = form.reason.data
            car_procedure_info.etc = form.ifetc.data
            car_procedure_info.driver = form.driver.data

            # 修改用车信息表的状态和节点
            car_procedure_info.state = 2
            car_procedure_info.current_line_node_id = 4
        # 保安确认出厂环节
        elif node == 4 and current_user.can(Permission.CONFIRM):
            # 修改审批表的state从1变更为2
            alter_approval_state = ProcedureApproval.query.filter_by(procedure_approval_flowid=procedure_id,
                                                                     procedure_approval_current_line_node_id=4,
                                                                     procedure_approval_state=1,
                                                                     ).first()
            alter_approval_state.procedure_approval_state = 2
            alter_approval_state.procedure_approval_user_id = current_user.id
            alter_approval_state.procedure_approval_approval_datetime = datetime.now()
            if form.L3approvereason.data:
                alter_approval_state.procedure_approval_reason = form.L3approvereason.data
            alter_approval_state.procedure_approval_approval_datetime = datetime.now()

            # 新增， 对用车审批表里的用车节点插入为5（保安入厂），state设置为1
            #  对流程进行流程名字拼接
            approval_name = car_procedure_info.users.username
            carnamepinjie = car_procedure_info.cars.name
            procedure_approval = ProcedureApproval(procedure_approval_flowid=procedure_id,
                                                   procedure_approval_flowname=approval_name + "的" + carnamepinjie + "用车流程申请",
                                                   procedure_approval_current_line_node_id=5,
                                                   procedure_approval_user_id=form.approvaluser.data,
                                                   # procedure_approval_reason=form.L3approvereason.data,
                                                   procedure_approval_flowmodal="carproceduremodal",
                                                   procedure_approval_approval_datetime=datetime.now(),
                                                   procedure_approval_state=1,
                                                   procedure_approval_company=current_user.company
                                                   )
            # 修改用车信息表的状态和节点
            if form.outmiles.data:
                car_procedure_info.outmiles = form.outmiles.data
            car_procedure_info.state = 3
            car_procedure_info.current_line_node_id = 5
            car_procedure_info.actual_start_datetime = datetime.now()

            # 保安确认入厂环节
        elif node == 5 and current_user.can(Permission.CONFIRM):
            # 修改审批表的state从1变更为2
            alter_approval_state = ProcedureApproval.query.filter_by(procedure_approval_flowid=procedure_id,
                                                                     procedure_approval_current_line_node_id=5,
                                                                     procedure_approval_state=1,
                                                                     ).first()
            alter_approval_state.procedure_approval_state = 2
            alter_approval_state.procedure_approval_user_id = current_user.id
            alter_approval_state.procedure_approval_approval_datetime = datetime.now()
            if form.L4approvereason.data:
                alter_approval_state.procedure_approval_reason = form.L4approvereason.data
            alter_approval_state.procedure_approval_approval_datetime = datetime.now()
            car_procedure_info.state = 4
            if form.miles.data:
                car_procedure_info.miles = form.miles.data
            car_procedure_info.actual_end_datetime = datetime.now()
            #     去流程状态表里修改运行中的状态为完成
            proedure_state = ProcedureState.query.filter_by(procedure_state_flowid=procedure_id).first()
            proedure_state.procedure_state = 2
            db.session.add(proedure_state)

        db.session.add(alter_approval_state)
        db.session.add(car_procedure_info)
        if node != 5:
            db.session.add(procedure_approval)
        try:
            db.session.commit()
            flash("您的用车申请已经审批成功，请到我的流程查看")
            return redirect(url_for("home.todolist"))
        except:
            db.session.rollback()
            flash("提交数据失败")
            abort(404)
        return redirect(url_for("home.todolist"))


# 快递流程申请表
@home.route("/procedureapproval2", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def procedureapproval2():
    # 生成快递流程申请表单对象
    form = PackageProcedureForm()
    # 对表单的提交内容进行验证
    if form.validate_on_submit():
        logistics_company = request.form.get("logistics_company")
        payment_method = request.form.get("payment_method")
        collect_person = request.form.get("collect_person")
        user = User.query.filter_by(username=collect_person).first()
        if user:
            collect_departmentid = user.departmentid
            if payment_method == "寄付":
                package_procedure_approval = PackageProcedureInfo(procedure_list_id=2,
                                                                  procedure_name="快递申请表",
                                                                  logistics_company=logistics_company,
                                                                  num=form.num.data,
                                                                  destination_company=form.destination_company.data,
                                                                  package_name=form.package_name.data,
                                                                  payment_method=payment_method,
                                                                  approval_departmentid=current_user.departmentid,
                                                                  approval_person=current_user.username,
                                                                  collect_person=collect_person,
                                                                  collect_departmentid=collect_departmentid,
                                                                  status="待寄出"

                                                                  )

                db.session.add(package_procedure_approval)
                try:
                    db.session.commit()
                    flash("您的快递流程已经处理成功，请到我的流程查看")
                    return redirect(url_for("home.indexlist"))
                except:
                    db.session.rollback()
                    flash("提交数据失败")
                    abort(404)
            elif payment_method == "到付":
                package_procedure_approval = PackageProcedureInfo(procedure_list_id=2,
                                                                  procedure_name="快递申请表",
                                                                  logistics_company=logistics_company,
                                                                  num=form.num.data,
                                                                  destination_company=form.destination_company.data,
                                                                  package_name=form.package_name.data,
                                                                  payment_method=payment_method,
                                                                  approval_departmentid=current_user.departmentid,
                                                                  approval_person=current_user.username,
                                                                  collect_person=collect_person,
                                                                  collect_departmentid=collect_departmentid,
                                                                  status="已收货",
                                                                  confirm_time=datetime.now()

                                                                  )

                db.session.add(package_procedure_approval)
                try:
                    db.session.commit()
                    flash("您的快递申请已经提交成功，请到我的流程查看")
                    return redirect(url_for("home.indexlist"))
                except:
                    db.session.rollback()
                    flash("提交数据失败")
                    abort(404)
        flash("您填写的寄件人/收件人不存在，请重新填写")

    return render_template("home/procedureapproval2.html", current_time=datetime.utcnow(), form=form,
                           )


# 快递流程申请表
@home.route("/packageproceduremodal", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def packageproceduremodal():
    # 生成快递流程申请表单对象，正常第一次使用模板时的get
    forminfo = PackageProcedureForm()
    forminfo.logistc_company.choices = [(c.id, c.company_name) for c in LogisticCompanyList.query.all()]
    forminfo.approvaluser.choices = [(c.id, c.username) for c in
                                     User.query.filter(User.company == current_user.company,

                                                       User.role_id.in_(["2"]))]
    procedure_id = request.args.get("procedure_id")
    procedure_door = request.args.get("procedure_door")
    # 以read形式进来的get
    if request.method == "GET":
        # 如果能找到流程id，查询该条快递申请的用车信息和审批信息
        if procedure_id:
            # 如果流程id存在，则找到这条记录
            myprocedure = PackageProcedureInfo.query.join(ProcedureApproval,
                                                          PackageProcedureInfo.id == ProcedureApproval.procedure_approval_flowid).add_entity(
                ProcedureApproval).join(User, PackageProcedureInfo.approval_user_id == User.id).add_entity(
                User).filter(PackageProcedureInfo.id == procedure_id).first()
            # 找到记录后，将查询到的值写入到前端页面。
            forminfo.logistc_company.data = myprocedure.PackageProcedureInfo.logistics_company_id
            forminfo.num.data = myprocedure.PackageProcedureInfo.num
            forminfo.package_name.data = myprocedure.PackageProcedureInfo.package_name
            forminfo.destination_company.data = myprocedure.PackageProcedureInfo.destination_company
            forminfo.collect_person.data = myprocedure.PackageProcedureInfo.collect_users.username
            forminfo.approvaluser.data = myprocedure.PackageProcedureInfo.approval_user_id
            forminfo.payment_method.data = myprocedure.PackageProcedureInfo.payment_method

            # 找到当前节点下可以驳回的选项
            rejectnodes = [(c.procedure_line_next_line_id, c.procedure_line_description) for c in
                           ProcedureLine.query.filter(
                               ProcedureLine.procedure_line_flowmodal == myprocedure.ProcedureApproval.procedure_approval_flowmodal,
                               ProcedureLine.procedure_line_pre_line_id == myprocedure.PackageProcedureInfo.current_line_node_id,
                               ProcedureLine.procedure_line_next_line_id < myprocedure.PackageProcedureInfo.current_line_node_id)]

            # 找到目前审批记录是否有审批记录
            L3approvalreasons = ProcedureApproval.query.join(User,
                                                             ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
                User).join(PackageProcedureInfo,
                           ProcedureApproval.procedure_approval_flowid == PackageProcedureInfo.id).add_entity(
                PackageProcedureInfo).filter(ProcedureApproval.procedure_approval_flowid == procedure_id,
                                             ProcedureApproval.procedure_approval_state == 2,
                                             ProcedureApproval.procedure_approval_current_line_node_id == 4
                                             )
            # 通过入门的只读属性判断是否是只读，在这个地方控制当前节点值，指定了第6个专属设置只读的节点，因为是通过节点控制权限。
            if procedure_door == "read":
                current_line_node_id = 6
            else:
                current_line_node_id = myprocedure.PackageProcedureInfo.current_line_node_id

            filedpermissions = FieldPermission.query.filter(
                FieldPermission.field_permission_node == current_line_node_id,
                FieldPermission.field_permission_flowmodal == "packageprocedure").all()
            for filedpermission in filedpermissions:
                if filedpermission.field_permission_read == "1":
                    # 获取字段权限表的字段名称
                    filedname = filedpermission.field_permission_field_name
                    # 找到Form中该字段对应的属性，并修改赋值其属性为不可用。
                    getattr(forminfo, filedname).render_kw = {"disabled": "disabled"}

            return render_template("home/packageproceduremodal.html", current_time=datetime.utcnow(), forminfo=forminfo,
                                   myprocedure=myprocedure, L3approvalreasons=L3approvalreasons,
                                   current_line_node_id=current_line_node_id,
                                   procedure_door=procedure_door, rejectnodes=rejectnodes)
        # 否则找不到流程id，我就返回空值，默认是新的流程申请。
        else:
            L3approvalreasons = False
            myprocedure = False
            current_line_node_id = 1
            return render_template("home/packageproceduremodal.html", current_time=datetime.utcnow(), forminfo=forminfo,
                                   myprocedure=myprocedure, current_line_node_id=current_line_node_id,
                                   L3approvalreasons=L3approvalreasons, procedure_door=procedure_door)
    # 对表单的提交内容进行验证
    # 用户post提交进入的界面
    if request.method == "POST":
        myprocedure = PackageProcedureInfo.query.join(ProcedureApproval,
                                                      PackageProcedureInfo.id == ProcedureApproval.procedure_approval_flowid).add_entity(
            ProcedureApproval).join(User, PackageProcedureInfo.approval_user_id == User.id).add_entity(
            User).filter(PackageProcedureInfo.id == procedure_id).first()
        # 员工在模板提交初次申请，或者对驳回的进行修改。
        if request.values.get("sbbtn") == "reject":
            rejectnode = request.form.get("rejectnode")
            reject_procedure_id = request.form.get("reject_procedure_id")
            rejectreason = request.form.get("rejectreason")
            # current_line_node_id = request.form.get("current_line_node_id")
            # 拿到快递信息表并修改节点为驳回节点
            package_procedure_info = PackageProcedureInfo.query.filter_by(id=reject_procedure_id).first()
            current_line_node_id = package_procedure_info.current_line_node_id
            package_procedure_info.current_line_node_id = rejectnode
            # 查找当前的审批节点,变更他的状态从1到2
            reject_procedure_close = ProcedureApproval.query.filter(
                ProcedureApproval.procedure_approval_flowid == reject_procedure_id,
                ProcedureApproval.procedure_approval_current_line_node_id == current_line_node_id,
                ProcedureApproval.procedure_approval_state == 1,
            ).first()

            reject_procedure_close.procedure_approval_state = 2
            reject_procedure_close.procedure_approval_reason = rejectreason
            reject_procedure_close.procedure_approval_user_id = current_user.id
            # 找到应该驳回的节点的那条审批记录，并找到该条记录的审批人。
            reject_procedure_close_pre = ProcedureApproval.query.filter(
                ProcedureApproval.procedure_approval_flowid == reject_procedure_id,
                ProcedureApproval.procedure_approval_current_line_node_id == rejectnode,
            ).first()

            rejectuserid = reject_procedure_close_pre.procedure_approval_user_id
            # 拼接用户姓名
            approval_name = package_procedure_info.approval_users.username
            namepinjie = package_procedure_info.package_name

            # 在审批表中新增驳回节点,状态为1
            reject_approval = ProcedureApproval(procedure_approval_flowid=reject_procedure_id,
                                                procedure_approval_flowname=approval_name + "的" + namepinjie + "快递流程申请",
                                                procedure_approval_current_line_node_id=rejectnode,
                                                procedure_approval_user_id=rejectuserid,

                                                procedure_approval_flowmodal="packageproceduremodal",
                                                procedure_approval_approval_datetime=datetime.now(),
                                                procedure_approval_state=1,
                                                procedure_approval_company=current_user.company
                                                )

            db.session.add(reject_approval)
            db.session.add(reject_procedure_close)
            db.session.add(reject_procedure_close_pre)

            try:
                db.session.commit()
                flash("您的快递申请已经驳回成功")
                return redirect(url_for("home.todolist"))
            except:
                db.session.rollback()
                flash("提交数据失败")
                abort(404)
            return redirect(url_for("home.todolist"))
        #     如果不是驳回正常进行审批，节点为1就是要进行驳回后的提交
        # 如果是点击了取消按钮，则进入以下流程。
        if request.values.get("sbbtn") == "cancel":
            cancel_procedure_id = request.form.get("cancel_procedure_id")
            cancelreason = request.form.get("cancelreason")

            # 拿到快递信息表并修改节点为取消状态
            package_procedure_info = PackageProcedureInfo.query.filter_by(id=cancel_procedure_id).first()
            current_line_node_id = package_procedure_info.current_line_node_id
            package_procedure_info.state = 5
            # 查找当前的审批节点,变更他的状态从1到2
            cancel_procedure_close = ProcedureApproval.query.filter(
                ProcedureApproval.procedure_approval_flowid == cancel_procedure_id,
                ProcedureApproval.procedure_approval_current_line_node_id == current_line_node_id,
                ProcedureApproval.procedure_approval_state == 1,
            ).first()

            cancel_procedure_close.procedure_approval_state = 2
            cancel_procedure_close.procedure_approval_reason = cancelreason
            cancel_procedure_close.procedure_approval_user_id = current_user.id
            #     去流程状态表里修改运行中的状态为完成
            proedure_state = ProcedureState.query.filter_by(procedure_state_flowid=cancel_procedure_id).first()
            proedure_state.procedure_state = 5
            # 体积修改对象
            db.session.add(proedure_state)
            db.session.add(package_procedure_info)
            db.session.add(cancel_procedure_close)

            try:
                db.session.commit()
                flash("您的快递申请已经取消成功")
                return redirect(url_for("home.todolist"))
            except:
                db.session.rollback()
                flash("提交数据失败")
                abort(404)
            return redirect(url_for("home.todolist"))
        # 如果能找到相关流程，证明不是第一次申请，则找到当前节点进行提交。
        if myprocedure:
            current_line_node_id = myprocedure.PackageProcedureInfo.current_line_node_id
            if forminfo.validate_on_submit() and current_line_node_id == 1:
                payment_method = request.form.get("payment_method")
                collect_person = forminfo.collect_person.data
                user = User.query.filter_by(username=collect_person).first()
                package_procedure_info = PackageProcedureInfo.query.filter(
                    PackageProcedureInfo.id == procedure_id).first()
                if user:
                    # 修改流程审批表里的信息
                    alter_approval_state = ProcedureApproval.query.filter_by(procedure_approval_flowid=procedure_id,
                                                                             procedure_approval_current_line_node_id=1,
                                                                             procedure_approval_state=1,
                                                                             ).first()
                    alter_approval_state.procedure_approval_state = 2
                    alter_approval_state.procedure_approval_user_id = current_user.id
                    alter_approval_state.procedure_approval_approval_datetime = datetime.now()
                    if forminfo.L3approvereason.data:
                        alter_approval_state.procedure_approval_reason = forminfo.L3approvereason.data
                    alter_approval_state.procedure_approval_approval_datetime = datetime.now()
                    # #     去流程状态表里修改运行中的状态为运行中
                    # procedure_state = ProcedureState.query.filter_by(procedure_state_flowid=procedure_id).first()
                    # procedure_state.procedure_state = 1
                    # db.session.add(procedure_state)

                    # 在审批表中新增第四个节点,状态为1
                    procedure_approval = ProcedureApproval(procedure_approval_flowid=procedure_id,
                                                           procedure_approval_flowname=alter_approval_state.procedure_approval_flowname,
                                                           procedure_approval_current_line_node_id=4,
                                                           procedure_approval_user_id=forminfo.approvaluser.data,
                                                           procedure_approval_flowmodal="packageproceduremodal",
                                                           procedure_approval_approval_datetime=datetime.now(),
                                                           procedure_approval_state=1,
                                                           procedure_approval_company=current_user.company
                                                           )
                    db.session.add(procedure_approval)
                    db.session.add(alter_approval_state)

                    # 根据提交内容，修改快递流程表里的信息
                    package_procedure_info.logistc_company = forminfo.logistc_company.data
                    package_procedure_info.num = forminfo.num.data
                    package_procedure_info.package_name = forminfo.package_name.data
                    package_procedure_info.destination_company = forminfo.destination_company.data
                    package_procedure_info.collect_user_id = user.id
                    # 修改快递申请表该条流程的状态为运行中。
                    package_procedure_info.state = 1
                    package_procedure_info.current_line_node_id = 4
                    package_procedure_info.confirm_time = datetime.now()

                    db.session.add(package_procedure_info)

                    try:
                        db.session.commit()
                        flash("您的快递流程已经处理成功，请到我的流程查看")
                        return redirect(url_for("home.todolist"))
                    except:
                        db.session.rollback()
                        flash("提交数据失败")
                        abort(404)
                flash("您填写的寄件人/收件人不存在，请重新填写")
                return render_template("home/packageproceduremodal.html", current_time=datetime.utcnow(),
                                       forminfo=forminfo,
                                       myprocedure=myprocedure, current_line_node_id=current_line_node_id,
                                       )
            if forminfo.validate_on_submit() and current_line_node_id == 4:
                payment_method = request.form.get("payment_method")
                collect_person = forminfo.collect_person.data
                user = User.query.filter_by(username=collect_person).first()
                package_procedure_info = PackageProcedureInfo.query.filter(
                    PackageProcedureInfo.id == procedure_id).first()

                if user:
                    # 修改流程审批表里的信息
                    alter_approval_state = ProcedureApproval.query.filter_by(procedure_approval_flowid=procedure_id,
                                                                             procedure_approval_current_line_node_id=4,
                                                                             procedure_approval_state=1,
                                                                             ).first()
                    alter_approval_state.procedure_approval_state = 2
                    alter_approval_state.procedure_approval_user_id = current_user.id
                    alter_approval_state.procedure_approval_approval_datetime = datetime.now()
                    if forminfo.L3approvereason.data:
                        alter_approval_state.procedure_approval_reason = forminfo.L3approvereason.data
                    alter_approval_state.procedure_approval_approval_datetime = datetime.now()
                    #     去流程状态表里修改运行中的状态为完成
                    procedure_state = ProcedureState.query.filter_by(procedure_state_flowid=procedure_id).first()
                    procedure_state.procedure_state = 2
                    db.session.add(procedure_state)
                    db.session.add(alter_approval_state)

                    # 根据提交内容，修改快递流程表里的信息
                    package_procedure_info.logistc_company = forminfo.logistc_company.data
                    package_procedure_info.num = forminfo.num.data
                    package_procedure_info.package_name = forminfo.package_name.data
                    package_procedure_info.destination_company = forminfo.destination_company.data
                    package_procedure_info.collect_user_id = user.id
                    # 修改快递申请表该条流程的状态为结束。
                    package_procedure_info.state = 2
                    package_procedure_info.confirm_time = datetime.now()

                    db.session.add(package_procedure_info)

                    try:
                        db.session.commit()
                        flash("您的快递流程已经处理成功，请到我的流程查看")
                        return redirect(url_for("home.todolist"))
                    except:
                        db.session.rollback()
                        flash("提交数据失败")
                        abort(404)
                flash("您填写的寄件人/收件人不存在，请重新填写")
                return render_template("home/packageproceduremodal.html", current_time=datetime.utcnow(),
                                       forminfo=forminfo,
                                       myprocedure=myprocedure, current_line_node_id=current_line_node_id,
                                       procedure_door=procedure_door
                                       )
            flash("提交不符合要求，请重新填写")
            return render_template("home/packageproceduremodal.html", current_time=datetime.utcnow(), forminfo=forminfo,
                                   myprocedure=myprocedure,
                                   current_line_node_id=1,
                                   procedure_door=procedure_door)
        # 找不到相关流程，则证明这是第一次申请，增加审批表1的完成节点2状态，增加审批表4的运行1状态。
        else:
            # 找不到相关流程，则认为这是一次全新的流程初次申请。
            if forminfo.validate_on_submit():

                payment_method = request.form.get("payment_method")
                collect_person = forminfo.collect_person.data
                user = User.query.filter_by(username=collect_person).first()
                if user:
                    collect_departmentid = user.departmentid
                    flowid = str(uuid.uuid1())
                    # 寄件人姓名
                    procedure_approval_flowname = user.username + forminfo.package_name.data + "快递申请表"
                    if payment_method == "寄付":
                        package_procedure_approval = PackageProcedureInfo(
                            id=flowid,
                            procedure_list_id=2,
                            procedure_list_flowmodal="packageproceduremodal",
                            procedure_name=procedure_approval_flowname,
                            logistics_company_id=forminfo.logistc_company.data,
                            num=forminfo.num.data,
                            destination_company=forminfo.destination_company.data,
                            package_name=forminfo.package_name.data,
                            payment_method=payment_method,
                            # approval_departmentid=current_user.departmentid,
                            approval_user_id=current_user.id,
                            collect_user_id=user.id,
                            collect_departmentid=collect_departmentid,
                            current_line_node_id=4,
                            state=1
                        )
                        # package = PackageProcedureInfo.query.filter_by(id=form.carname.data).first()

                        procedure_approval1 = ProcedureApproval(procedure_approval_flowid=flowid,
                                                                procedure_approval_flowname=procedure_approval_flowname,
                                                                procedure_approval_current_line_node_id=1,
                                                                procedure_approval_user_id=current_user.id,
                                                                procedure_approval_flowmodal="packageproceduremodal",
                                                                procedure_approval_approval_datetime=datetime.now(),
                                                                procedure_approval_state=2,
                                                                procedure_approval_company=current_user.company
                                                                )
                        procedure_approval = ProcedureApproval(procedure_approval_flowid=flowid,
                                                               procedure_approval_flowname=procedure_approval_flowname,
                                                               procedure_approval_current_line_node_id=4,
                                                               procedure_approval_user_id=forminfo.approvaluser.data,
                                                               procedure_approval_flowmodal="packageproceduremodal",
                                                               procedure_approval_approval_datetime=datetime.now(),
                                                               procedure_approval_state=1,
                                                               procedure_approval_company=current_user.company
                                                               )
                        procedure_state = ProcedureState(
                            procedure_state_flowid=flowid,
                            procedure_state_name=procedure_approval_flowname,
                            procedure_state=1,
                            procedure_state_flowmodal="packageproceduremodal",
                            procedure_state_procedure_list_name="快递申请表",
                            procedure_state_user_id=current_user.id,
                            procedure_state_approval_datetime=datetime.now()

                        )

                        db.session.add(procedure_approval1)
                        db.session.add(procedure_approval)
                        db.session.add(procedure_state)
                        db.session.add(package_procedure_approval)
                        try:
                            db.session.commit()
                            flash("您的快递流程已经处理成功，请到我的流程查看")
                            return redirect(url_for("home.todolist"))
                        except:
                            db.session.rollback()
                            flash("提交数据失败")
                            abort(404)
                    elif payment_method == "到付":
                        package_procedure_approval = PackageProcedureInfo(id=flowid,
                                                                          procedure_list_id=2,
                                                                          procedure_list_flowmodal="packageproceduremodal",
                                                                          procedure_name=procedure_approval_flowname,
                                                                          logistics_company_id=forminfo.logistc_company.data,
                                                                          num=forminfo.num.data,
                                                                          destination_company=forminfo.destination_company.data,
                                                                          package_name=forminfo.package_name.data,
                                                                          payment_method=payment_method,
                                                                          # approval_departmentid=current_user.departmentid,
                                                                          approval_user_id=current_user.id,
                                                                          collect_user_id=user.id,
                                                                          collect_departmentid=collect_departmentid,
                                                                          current_line_node_id=4,
                                                                          state=2,
                                                                          confirm_time=datetime.now()

                                                                          )
                        procedure_approval1 = ProcedureApproval(procedure_approval_flowid=flowid,
                                                                procedure_approval_flowname=procedure_approval_flowname,
                                                                procedure_approval_current_line_node_id=1,
                                                                procedure_approval_user_id=current_user.id,
                                                                procedure_approval_flowmodal="packageproceduremodal",
                                                                procedure_approval_approval_datetime=datetime.now(),
                                                                procedure_approval_state=2,
                                                                procedure_approval_company=current_user.company
                                                                )

                        procedure_approval = ProcedureApproval(procedure_approval_flowid=flowid,
                                                               procedure_approval_flowname=procedure_approval_flowname,
                                                               procedure_approval_current_line_node_id=4,
                                                               procedure_approval_user_id=forminfo.approvaluser.data,
                                                               procedure_approval_flowmodal="packageproceduremodal",
                                                               procedure_approval_approval_datetime=datetime.now(),
                                                               procedure_approval_state=2,
                                                               procedure_approval_company=current_user.company
                                                               )
                        procedure_state = ProcedureState(
                            procedure_state_flowid=flowid,
                            procedure_state_name=procedure_approval_flowname,
                            procedure_state=2,
                            procedure_state_flowmodal="packageproceduremodal",
                            procedure_state_procedure_list_name="快递申请表",
                            procedure_state_user_id=current_user.id

                        )
                        db.session.add(procedure_approval1)
                        db.session.add(procedure_approval)
                        db.session.add(procedure_state)
                        db.session.add(package_procedure_approval)
                        try:
                            db.session.commit()
                            flash("您的快递申请已经提交成功，请到我的流程查看")
                            return redirect(url_for("home.todolist"))
                        except:
                            db.session.rollback()
                            flash("提交数据失败")
                            abort(404)
                flash("您填写的寄件人/收件人不存在，请重新填写")
            flash("提交不符合要求，请重新填写")
            return render_template("home/packageproceduremodal.html", current_time=datetime.utcnow(), forminfo=forminfo,
                                   myprocedure=myprocedure,
                                   current_line_node_id=1,
                                   procedure_door=procedure_door)


# 会议室预约申请表
@home.route("/procedureapproval3", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def procedureapproval3():
    choices = times
    return render_template("home/procedureapproval3.html", current_time=datetime.utcnow(), choices=choices)


# 我的已经审批过的流程清单
@home.route("/myapprovaledprocedure", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L1_APPROVAL)
def myapprovaledprocedure():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")
    if not current_user.can(Permission.L2_APPROVAL):
        pagination = CarProcedureInfo.query.filter(CarProcedureInfo.departmentid == current_user.departmentid,
                                                   CarProcedureInfo.approval_time.contains(keywords),
                                                   CarProcedureInfo.first_approval == current_user.id,
                                                   CarProcedureInfo.status1 == 1,

                                                   ).order_by(
            CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        my_procedure = pagination.items
    else:
        pagination = CarProcedureInfo.query.filter(and_(
            CarProcedureInfo.approval_time.contains(keywords),
            or_(
                CarProcedureInfo.first_approval == current_user.id,
                CarProcedureInfo.second_approval == current_user.id,
            ),
            or_(
                CarProcedureInfo.status1 == 1,
                CarProcedureInfo.status2 == 1,
            )
        )

        ).order_by(
            CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        my_procedure = pagination.items

    return render_template("home/myapprovaledprocedure.html", my_procedure=my_procedure, pagination=pagination, )


# 用车所有流程清导出界面单页
@home.route("/procedurelists", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def procedurelists():
    if request.method == "POST":
        year = request.form.get("year1")
        month = request.form.get("month1")
        arrays = CarProcedureInfo.query.filter(
            extract("year", CarProcedureInfo.actual_end_datetime) == year,
            extract("month", CarProcedureInfo.actual_end_datetime) == month,
            CarProcedureInfo.company == current_user.company,
            CarProcedureInfo.state == 4

        ).order_by(
            CarProcedureInfo.actual_end_datetime.asc()).all()
        if arrays:  # 如果有数据则导出
            column = [["序号", "流程编号", "申请人", "驾驶员", "目的地", "用车原因", "车型", "是否用ETC", "出厂公里数", "入厂公里数",
                       "出厂时间", "入厂时间", "公司"]]
            i = 1
            for array in arrays:
                list = array.jsonstr()  # 将每一行查询的数据转换成字典格式
                array_content = [i,
                                 list["id"],
                                 list["user_name"],
                                 list["driver"],
                                 list["arrival_place"],
                                 list["reason"],
                                 list["car_name"],
                                 list["etc"],
                                 list["outmiles"],
                                 list["miles"],
                                 list["actual_start_datetime"],
                                 list["actual_end_datetime"],
                                 list["company"],
                                 ]  # 将每一行的数据需要的先转换成字典，然后把相应内容导出。
                column.append(array_content)
                i += 1
                filename = "用车情况按月统计表" + datetime.now().__str__()[0:10]

            return excel.make_response_from_array(column, file_type="xls", file_name=filename)
        else:
            flash("该月份没有用车记录")
            return redirect(url_for("home.procedurelists"))
    if request.method == "GET":
        return render_template("home/procedurelists.html")


# 快递所有流程清导出界面单页
@home.route("/packageprocedurelists", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def packageprocedurelists():
    if request.method == "POST":
        year = request.form.get("year2")
        month = request.form.get("month2")
        arrays = PackageProcedureInfo.query.filter(
            extract("year", PackageProcedureInfo.confirm_time) == year,
            extract("month", PackageProcedureInfo.confirm_time) == month

        ).order_by(
            PackageProcedureInfo.approval_time.asc()).all()
        if arrays:  # 如果有数据则导出
            column = [
                ["序号", "流程编号", "申请时间", "申请人", "申请部门", "物流公司", "对方公司", "邮寄物品",
                 "运单号", "付款方式", "收/寄件人", "收/寄件部门", "确认邮寄/收货时间"]]
            i = 1
            for array in arrays:
                list = array.jsonstr()  # 将每一行查询的数据转换成字典格式
                array_content = [i,
                                 list["id"],
                                 list["approval_time"][0:10],
                                 list["approval_person"],
                                 list["approval_department"],
                                 list["logistics_company"],
                                 list["destination_company"],
                                 list["package_name"],
                                 list["num"],
                                 list["payment_method"],
                                 list["collect_person"],
                                 list["collect_department"],
                                 list["confirm_time"][0:10],
                                 ]  # 将每一行的数据需要的先转换成字典，然后把相应内容导出。
                column.append(array_content)
                i += 1
                filename = "快递情况按月统计表" + datetime.now().__str__()[0:10]

            return excel.make_response_from_array(column, file_type="xls", file_name=filename)
        else:
            flash("该月份没有快递记录")
            return redirect(url_for("home.procedurelists"))
    if request.method == "GET":
        return render_template("home/procedurelists.html")


# 用户登出
@home.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()

    return redirect(url_for("home.login"))


# 用户修改密码
@home.route("/resetpwd", methods=["GET", "POST"])
@login_required
def resetpwd():
    form = ResetPwd()

    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data):
            current_user.password = form.password2.data
            db.session.add(current_user)
            try:
                db.session.commit()
                flash("您已经成功修改密码")


            except:
                db.session.rollback()
                flash("数据提交失败，请联系管理员")

        else:
            flash("旧密码错误，请重新输入")
    return render_template("home/resetpwd.html", form=form)


# 用户管理界面
@home.route("/usermanage", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def usermanage():
    # 生成增加新用户的form表单
    form = AddNewUserForm()
    formalteruser = AlterUserForm()
    formalteruser.alterdepartment.choices = [(c.id, c.department) for c in
                                             CompanyDepartment.query.filter_by(company=current_user.company, status=1)]
    formalteruser.alterroleid.choices = [(c.id, c.name) for c in
                                         Role.query.all()]
    form.department.choices = [(c.id, c.department) for c in
                               CompanyDepartment.query.filter_by(company=current_user.company, status=1)]
    form.roleid.choices = [(c.id, c.name) for c in
                           Role.query.all()]
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")
    userstatus = request.args.get("userstatus", "正常")
    # 修改完毕后提交员工信息
    if formalteruser.validate_on_submit():
        # 从提交的隐藏信息里获取用户id
        user_id = request.form.get("user_id")
        # 根据流程id找到该条记录
        user = User.query.filter(
            User.id == user_id,
        ).first()
        # 对该条记录的status1进行更新
        user.username = formalteruser.altername.data
        user.departmentid = formalteruser.alterdepartment.data
        user.tel = formalteruser.altertel.data
        user.role_id = formalteruser.alterroleid.data
        usersttusid = formalteruser.alterstatus.data
        if usersttusid == 1:
            user.status = "正常"
        elif usersttusid == 0:
            user.status = "删除"
        db.session.add(user)
        name = user.username
        try:
            db.session.commit()
            flash("你已修改员工{0}的信息".format(name))
        except:
            db.session.rollback()
            flash("修改信息失败")
            return render_template("404.html")

    pagination = User.query.filter(User.username.contains(keywords),
                                   User.status == userstatus,
                                   User.company == current_user.company,
                                   ).order_by(
        User.id.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    users = pagination.items
    # 获取部门的id并找到部门名称
    # departmentid = request.form.get("department")
    # departments = CompanyDepartment.query.filter_by(id=departmentid).first()
    # department = departments.department
    # 新增用户的表单通过验证并添加
    if form.validate_on_submit():
        newuser = User(username=form.name.data,
                       departmentid=form.department.data,
                       role_id=form.roleid.data,
                       tel=form.tel.data,
                       password="123456",
                       status="正常",
                       company=current_user.company
                       )
        db.session.add(newuser)
        try:
            db.session.commit()
            flash("您已添加新员工{0}，密码为123456".format(form.name.data))
        except:
            db.session.rollback()
            flash("用户已存在，添加失败")
            return render_template("404.html")
        return redirect(url_for("home.usermanage"))
    # 对删除和重置的员工进行操作。
    if request.args.get("user_id") and request.args.get("target"):
        user_id = request.args.get("user_id")
        user = User.query.filter(
            User.id == user_id,
        ).first()
        if request.args.get("target") == "del":
            # 对该条记录的status进行更新
            user.status = "删除"
        elif request.args.get("target") == "reset":
            user.password = "123456"
        db.session.add(user)
        name = user.username
        try:
            db.session.commit()
            if request.args.get("target") == "del":
                flash("你已删除{0}员工".format(name))
            elif request.args.get("target") == "reset":
                flash("你已重置员工{0}密码为123456".format(name))
        except:
            db.session.rollback()
            flash("删除/重置失败，请联系管理员")
            return render_template("404.html")
        return redirect(url_for("home.usermanage"))

    return render_template("home/usermanage.html", users=users, pagination=pagination, form=form,
                           formalteruser=formalteruser, keywords=keywords, userstatus=userstatus)

    # 部门管理界面


@home.route("/departmentmanage", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def departmentmanage():
    # 生成增加新用户的form表单

    formaddnew = AddNewDepartmentForm()
    formalterdepartment = AlterDepartmentForm()
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")
    departmentstatus = request.args.get("departmentstatus", "1")
    # 修改完毕后提交员工信息
    if formalterdepartment.validate_on_submit():
        # 从提交的隐藏信息里获取用户id
        department_id = request.form.get("department_id")
        # 根据流程id找到该条记录
        department = CompanyDepartment.query.filter(
            CompanyDepartment.id == department_id,
        ).first()
        # 对该条记录的status1进行更新
        department.department = formalterdepartment.alterdepartmentname.data
        department.status = formalterdepartment.alterstatus.data
        db.session.add(department)
        departmentname = department.department
        try:
            db.session.commit()
            flash("你已修改部门{0}的信息".format(departmentname))
        except:
            db.session.rollback()
            flash("修改信息失败")
            return render_template("404.html")
    pagination = CompanyDepartment.query.filter(CompanyDepartment.department.contains(keywords),
                                                CompanyDepartment.status == departmentstatus,
                                                CompanyDepartment.company == current_user.company,
                                                ).order_by(
        CompanyDepartment.id.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    departments = pagination.items
    if formaddnew.validate_on_submit():
        newdepartment = CompanyDepartment(company=current_user.company,
                                          department=formaddnew.newdepartment.data,
                                          status="1",
                                          )
        db.session.add(newdepartment)
        try:
            db.session.commit()
            flash("您已添加新部门{0}".format(formaddnew.newdepartment.data))
        except:
            db.session.rollback()
            flash("部门已存在，添加失败")
            return render_template("404.html")
        return redirect(url_for("home.departmentmanage"))
    # 对删除和重置的员工进行操作。
    if request.args.get("department_id") and request.args.get("target"):
        department_id = request.args.get("department_id")
        department = CompanyDepartment.query.filter(
            CompanyDepartment.id == department_id,
        ).first()
        if request.args.get("target") == "del":
            # 对该条记录的status进行更新
            department.status = "0"

        db.session.add(department)
        departmentname = department.department
        try:
            db.session.commit()
            if request.args.get("target") == "del":
                flash("你已删除{0}部门".format(departmentname))
        except:
            db.session.rollback()
            flash("删除/重置失败，请联系管理员")
            return render_template("404.html")
        return redirect(url_for("home.departmentmanage"))

    return render_template("home/departmentmanage.html", departments=departments, pagination=pagination,
                           formaddnew=formaddnew,
                           formalterdepartment=formalterdepartment, keywords=keywords,
                           departmentstatus=departmentstatus)


# 修改用户信息ajax
@home.route("/alteruser", methods=["POST"])
@login_required
def alteruser():
    data1 = json.loads(request.get_data())
    user_id = data1["user_id"]
    userinfos = User.query.filter(
        User.id == user_id,
    ).first()
    data = userinfos.jsonstr()
    return jsonify(data)


# 修改部门信息ajax
@home.route("/alterdepartment", methods=["POST"])
@login_required
def alterdepartment():
    data1 = json.loads(request.get_data())
    department_id = data1["department_id"]
    departmentinfos = CompanyDepartment.query.filter(
        CompanyDepartment.id == department_id,
    ).first()
    data = departmentinfos.jsonstr()
    return jsonify(data)


#
# 会议室预订
@home.route("/meetproceduremodal", methods=["GET", "POST"])
@login_required
def meetproceduremodal():
    date = request.args.get('time')
    now = datetime.now().date()
    if request.is_xhr:
        data = json.loads(request.get_data())
        add_dic = data['add_dic']
        del_dic = data['del_dic']
        date = data['date']
        date = date or now
        if del_dic:  # 拿到要删除的字典，然后删除
            for key, value in del_dic.items():
                for ele in value:
                    Order.query.filter_by(date=date, user_id=request.user.id, house_id=int(key),
                                          time=int(ele)).delete()
    if request.method == "POST":
        date = request.args.get("time")
    date = date or now
    username = current_user.id
    orders = Order.query.filter_by(date=date)
    houses = House.query.all()
    choices = times
    # data_list = []
    tablebody = ""
    for house in houses:  # 这就是构建表体数据
        tablebody += '<tr class="%s"><td>%s(%s)</td>' % (house.id, house.name, house.size)
        for choice in choices:
            for order in orders:
                if order.house_id == house.id and choice[0] == order.time:
                    if username == order.user_id:
                        tt = '<td class="nn danger"><span class="%s">%s</span></td>' % (choice[0], order.users.username)
                        break
                    else:
                        tt = '<td class="nn warning"><span class="%s">%s</span></td>' % (
                            choice[0], order.users.username)
                        break
                else:
                    tt = '<td class="nn"><span class="%s"></span></td>' % choice[0]
            tt = tt or '<td ></td>'
            tablebody += tt
        tablebody += '</tr>'
    tablebody = Markup(tablebody)

    return render_template("home/procedureapproval3.html", tablebody=tablebody, choices=choices)
