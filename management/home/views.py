from flask import render_template, redirect, url_for, abort, flash, request, \
    current_app, make_response, g, session, Response, jsonify, json
from .forms import LoginForm, ResetPwd, CarProcedureForm, MilesForm, AddNewUserForm, PackageProcedureForm, OutMilesForm, \
    L2approvalnok, AlterUserForm
from flask_login import login_required, current_user, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_, or_, extract, func
from ..models import Permission, Role, User, CarProcedureInfo, CarList, ProcedureList, PackageProcedureInfo, \
    CompanyDepartment, times, ProcedureApproval, ProcedureLine, ProcedureNode, ProcedureState, FieldPermission
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


# 用户主页
@home.route("/indexlist", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def indexlist():
    num = {}
    # 第一个流程---用车流程的总数量和运行数量
    p1num = CarProcedureInfo.query.filter(CarProcedureInfo.user_id == current_user.id).count()

    p1numusing = CarProcedureInfo.query.join(ProcedureApproval,
                                             CarProcedureInfo.id == ProcedureApproval.procedure_approval_id).filter(
        CarProcedureInfo.user_id == current_user.id,
        or_(
            ProcedureApproval.procedure_approval_current_line_node_id == 1,
            ProcedureApproval.procedure_approval_current_line_node_id == 2,

        ),
    ).count()
    # 第二个流程---快递流程的总数量和运行数量
    p2num = PackageProcedureInfo.query.filter(PackageProcedureInfo.collect_person == current_user.username).count()
    p2numusing = PackageProcedureInfo.query.filter(PackageProcedureInfo.collect_person == current_user.username,
                                                   PackageProcedureInfo.status == "待寄出").count()
    # 放一个字典，存放所有流程的总数量和正在使用的流程的数量，存放用车流程的数量
    num["p1"] = p1num
    num["p12"] = p1numusing
    # 存放快递流程的数量
    num["p2"] = p2num
    num["p22"] = p2numusing
    return render_template("home/indexlist.html", num=num)


# 门卫确认流程主页
@home.route("/confirmlist", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def confirmlist():
    num = {}
    # 第一个流程---用车流程的总数量和运行数量
    p1num = CarProcedureInfo.query.filter(CarProcedureInfo.user_id == current_user.id).count()
    p1numusing = CarProcedureInfo.query.filter(CarProcedureInfo.status2 == 1,
                                               CarProcedureInfo.company == current_user.company,
                                               CarProcedureInfo.actual_end_datetime == None).count()
    # 第二个流程---快递流程的总数量和运行数量
    p2num = PackageProcedureInfo.query.filter(PackageProcedureInfo.collect_person == current_user.username).count()
    p2numusing = PackageProcedureInfo.query.filter(PackageProcedureInfo.status == "待寄出").count()
    # 放一个字典，存放所有流程的总数量和正在使用的流程的数量，存放用车流程的数量
    num["p1"] = p1num
    num["p12"] = p1numusing
    # 存放快递流程的数量
    num["p2"] = p2num
    num["p22"] = p2numusing
    return render_template("home/confirmlist.html", num=num)


# 用车流程主页
@home.route("/carindex", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def carindex():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")

    pagination = CarProcedureInfo.query.join(ProcedureApproval,
                                             CarProcedureInfo.id == ProcedureApproval.procedure_approval_id).join(
        ProcedureLine,
        ProcedureApproval.procedure_approval_current_line_node_id == ProcedureLine.procedure_line_id).filter(
        CarProcedureInfo.user_id == current_user.id,
        CarProcedureInfo.approval_time.contains(keywords),
        # or_(
        #     ProcedureApproval.current_line_node_id == 1,
        #     ProcedureApproval.current_line_node_id == 2,
        #
        # )
        ProcedureApproval.procedure_approval_current_line_node_id.in_(["1", "2"])
    ).order_by(
        CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    my_procedure = pagination.items

    return render_template("home/carindex.html", my_procedure=my_procedure, pagination=pagination)


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
        ).order_by(
            ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        daibanno = ProcedureApproval.query.filter(
            ProcedureApproval.procedure_approval_state == 1).count()
        session["daibanno"] = daibanno
    #     保安可以看见自己相关的信息
    elif current_user.role_id == 2:
        pagination = ProcedureApproval.query.join(CarProcedureInfo,
                                                  ProcedureApproval.procedure_approval_flowid == CarProcedureInfo.id).add_entity(
            CarProcedureInfo).filter(
            ProcedureApproval.procedure_approval_current_line_node_id.in_(["4", "5"]),
            ProcedureApproval.procedure_approval_state == 1,
        ).order_by(
            ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        daibanno = ProcedureApproval.query.filter(
            ProcedureApproval.procedure_approval_current_line_node_id.in_(["4", "5"]),
            ProcedureApproval.procedure_approval_state == 1).count()
        session["daibanno"] = daibanno
    #     普通用户和经理可以看见自己的待办信息
    else:
        pagination = ProcedureApproval.query.join(User,
                                                  ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
            User).filter(
            ProcedureApproval.procedure_approval_user_id == current_user.id,

            ProcedureApproval.procedure_approval_state.in_(["0", "1"]),
        ).order_by(
            ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        daibanno = ProcedureApproval.query.filter(
            ProcedureApproval.procedure_approval_user_id == current_user.id,
            ProcedureApproval.procedure_approval_state == 1).count()
        session["daibanno"] = daibanno
    my_procedure = pagination.items

    return render_template("home/todolist.html", my_procedure=my_procedure, pagination=pagination)


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

        pagination = ProcedureApproval.query.join(User,
                                                  ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
            User).join(ProcedureState,
                       ProcedureApproval.procedure_approval_flowid == ProcedureState.procedure_state_flowid).add_entity(
            ProcedureState).filter(

            ProcedureApproval.procedure_approval_current_line_node_id == 1,
            ProcedureApproval.procedure_approval_flowname.contains(procedurename),
            ProcedureApproval.procedure_approval_approval_datetime.contains(proceduredate),
            ProcedureState.procedure_state.contains(procedurestate),

        ).with_entities(

            ProcedureApproval.procedure_approval_flowid,
            ProcedureApproval.procedure_approval_flowname,
            ProcedureState.procedure_state,
            func.max(ProcedureApproval.procedure_approval_approval_datetime).label("approval_datetime"),
            ProcedureApproval.procedure_approval_flowmodal,
        ).group_by(ProcedureApproval.procedure_approval_flowid).order_by(
            ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
    else:
        pagination = ProcedureApproval.query.join(User,
                                                  ProcedureApproval.procedure_approval_user_id == User.id).add_entity(
            User).join(ProcedureState,
                       ProcedureApproval.procedure_approval_flowid == ProcedureState.procedure_state_flowid).add_entity(
            ProcedureState).filter(
            ProcedureApproval.procedure_approval_user_id == current_user.id,
            ProcedureApproval.procedure_approval_current_line_node_id == 1,
            ProcedureApproval.procedure_approval_flowname.contains(procedurename),
            ProcedureApproval.procedure_approval_approval_datetime.contains(proceduredate),
            ProcedureState.procedure_state.contains(procedurestate),

        ).with_entities(

            ProcedureApproval.procedure_approval_flowid,
            ProcedureApproval.procedure_approval_flowname,
            ProcedureState.procedure_state,
            func.max(ProcedureApproval.procedure_approval_approval_datetime).label("approval_datetime"),
            ProcedureApproval.procedure_approval_flowmodal,
        ).group_by(ProcedureApproval.procedure_approval_flowid).order_by(
            ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)

    my_procedure = pagination.items

    return render_template("home/myprocedures.html", my_procedure=my_procedure, pagination=pagination,
                           procedurename=procedurename,
                           procedurestate=procedurestate, proceduredate=proceduredate)


# 我的所有已办流程（不是发起，而是经过审批的流程）
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
        User).join(ProcedureApproval,
                   ProcedureState.procedure_state_flowid == ProcedureApproval.procedure_approval_flowid).add_entity(
        ProcedureApproval).filter(
        ProcedureState.procedure_state_flowid.in_(list),

        ProcedureApproval.procedure_approval_current_line_node_id == 1,
        ProcedureApproval.procedure_approval_flowname.contains(procedurename),
        ProcedureApproval.procedure_approval_approval_datetime.contains(proceduredate),
        ProcedureState.procedure_state.contains(procedurestate),

    ).with_entities(

        ProcedureState.procedure_state_name,
        ProcedureState.procedure_state,
        User.username,
        func.max(ProcedureApproval.procedure_approval_approval_datetime).label("approval_datetime"),
        ProcedureState.procedure_state_flowmodal,
        ProcedureState.procedure_state_flowid,
    ).group_by(ProcedureApproval.procedure_approval_flowid).order_by(
        ProcedureApproval.procedure_approval_approval_datetime.desc()).paginate(page, per_page=current_app.config
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
                                                   User.department == current_user.department,
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
                                                  department=current_user.department,
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
                                                procedure_approval_state=2
                                                )
        procedure_approval = ProcedureApproval(procedure_approval_flowid=flowid,
                                               procedure_approval_flowname=current_user.username + "的" + car.name + "用车流程申请",
                                               procedure_approval_current_line_node_id=2,
                                               procedure_approval_user_id=form.approvaluser.data,
                                               procedure_approval_flowmodal="carproceduremodal",
                                               procedure_approval_approval_datetime=datetime.now(),
                                               procedure_approval_state=1
                                               )
        procedure_state = ProcedureState(
            procedure_state_flowid=flowid,
            procedure_state_name=current_user.username + "的" + car.name + "用车流程申请",
            procedure_state=1,
            procedure_state_flowmodal="carproceduremodal",
            procedure_state_procedure_list_name="公务用车申请表",
            procedure_state_user_id=current_user.id

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
            ProcedureApproval).filter(CarProcedureInfo.id == procedure_id).first()
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
                                                               User.department == current_user.department,
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
                                                procedure_approval_state=1
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
                                                   procedure_approval_state=1
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
                                                   procedure_approval_state=1
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
                                                   procedure_approval_state=1
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
                                                   procedure_approval_state=1
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
            collect_department = user.department
            if payment_method == "寄付":
                package_procedure_approval = PackageProcedureInfo(procedure_list_id=2,
                                                                  procedure_name="快递申请表",
                                                                  logistics_company=logistics_company,
                                                                  num=form.num.data,
                                                                  destination_company=form.destination_company.data,
                                                                  package_name=form.package_name.data,
                                                                  payment_method=payment_method,
                                                                  approval_department=current_user.department,
                                                                  approval_person=current_user.username,
                                                                  collect_person=collect_person,
                                                                  collect_department=collect_department,
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
                                                                  approval_department=current_user.department,
                                                                  approval_person=current_user.username,
                                                                  collect_person=collect_person,
                                                                  collect_department=collect_department,
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


# 会议室预约申请表
@home.route("/procedureapproval3", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def procedureapproval3():
    choices = times
    return render_template("home/procedureapproval3.html", current_time=datetime.utcnow(), choices=choices)


# 1级与2级待审批界面
@home.route("/L1L2approval", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L1_APPROVAL)
def L1L2approval():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")

    if not current_user.can(Permission.L2_APPROVAL):
        pagination = CarProcedureInfo.query.filter(CarProcedureInfo.department == current_user.department,
                                                   CarProcedureInfo.approval_time.contains(keywords),
                                                   CarProcedureInfo.status1 == 0,
                                                   CarProcedureInfo.company == current_user.company,

                                                   ).order_by(
            CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        my_procedure = pagination.items
    else:
        pagination = CarProcedureInfo.query.filter(and_(
            CarProcedureInfo.approval_time.contains(keywords),
            CarProcedureInfo.company == current_user.company,
            CarProcedureInfo.status1 != 2,
            CarProcedureInfo.status2 != 2,
            or_(CarProcedureInfo.status1 == 0,
                CarProcedureInfo.status2 == 0, ))
        ).order_by(
            CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        my_procedure = pagination.items

    return render_template("home/L1L2approval.html", my_procedure=my_procedure, pagination=pagination)


# 一级审批确认通过流程
@home.route("/L1approvalok/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L1_APPROVAL)
def L1approvalok(procedure_id):
    # 根据流程id找到该条记录
    procedure = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    # 对该条记录的status1进行更新
    procedure.status1 = 1
    procedure.first_approval = current_user.id

    db.session.add(procedure)
    try:
        db.session.commit()
        flash("您已审批通过一条申请")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("home/../templates/404.html")

    return redirect(url_for("home.L1L2approval"))


# 一级审批拒绝流程
@home.route("/L1approvalnok/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L1_APPROVAL)
def L1approvalnok(procedure_id):
    # 根据流程id找到该条记录
    procedure = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    # 对该条记录的status1进行更新
    procedure.status1 = 2
    procedure.first_approval = current_user.id
    db.session.add(procedure)
    try:
        db.session.commit()
        flash("您已拒绝一条申请")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("home/../templates/404.html")

    return redirect(url_for("home.L1L2approval"))


# 二级审批确认通过流程
@home.route("/L2approvalok/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def L2approvalok(procedure_id):
    # 根据流程id找到该条记录
    procedure = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    # 对该条记录的status1进行更新
    procedure.status2 = 1
    procedure.second_approval = current_user.id
    db.session.add(procedure)
    try:
        db.session.commit()
        flash("您已审批通过一条申请")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("home/../templates/404.html")

    return redirect(url_for("home.L1L2approval"))


# 二级审批拒绝流程
@home.route("/L2approvalnok", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def L2approvalnok():
    # 根据流程id找到该条记录
    if request.form.get("rejectreason"):
        procedure_id = request.form.get("procedure_id")
        rejectreason = request.form.get("rejectreason")
        procedure = CarProcedureInfo.query.filter(
            CarProcedureInfo.id == procedure_id,
        ).first()
        # 对该条记录的status1进行更新
        procedure.status2 = 2
        procedure.second_approval = current_user.id
        procedure.rejectreason = rejectreason
        db.session.add(procedure)
        try:
            db.session.commit()
            flash("您已拒绝一条申请")
        except:
            db.session.rollback()
            flash("提交数据失败")
            return render_template("home/../templates/404.html")

    return redirect(url_for("home.L1L2approval"))


# 我的已经审批过的流程清单
@home.route("/myapprovaledprocedure", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L1_APPROVAL)
def myapprovaledprocedure():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")
    if not current_user.can(Permission.L2_APPROVAL):
        pagination = CarProcedureInfo.query.filter(CarProcedureInfo.department == current_user.department,
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


# 确认车辆入厂流程操作界面
@home.route("/confirmcar", methods=["GET", "POST"])
@login_required
@permission_required(Permission.CONFIRM)
def confirmcar():
    page = request.args.get("page", 1, type=int)
    # keywords = request.args.get("keywords", "")
    form = MilesForm()
    form2 = OutMilesForm()
    if form.validate_on_submit():
        miles = form.miles.data
        procedure_id = form.procedure_id.data
        a = CarProcedureInfo.query.filter(
            CarProcedureInfo.id == procedure_id,

        ).first()
        a.miles = miles
        a.actual_end_datetime = datetime.now()
        db.session.add(a)
        try:
            db.session.commit()
            flash("您已确认车辆进厂，公里数提交成功")
        except:
            db.session.rollback()
            flash("提交数据失败")
            return render_template("404.html")

    pagination = CarProcedureInfo.query.filter(
        # CarProcedureInfo.approval_time.contains(keywords),
        CarProcedureInfo.status2 == 1,
        CarProcedureInfo.company == current_user.company,
        CarProcedureInfo.actual_end_datetime == None,

    ).order_by(
        CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    my_procedure = pagination.items

    return render_template("home/confirmcar.html", my_procedure=my_procedure, pagination=pagination, form=form,
                           form2=form2)


# 确认车辆出厂流程操作界面
@home.route("/confirmoutcar", methods=["GET", "POST"])
@login_required
@permission_required(Permission.CONFIRM)
def confirmoutcar():
    page = request.args.get("page", 1, type=int)
    form = MilesForm()
    form2 = OutMilesForm()

    outmiles = form2.outmiles.data
    procedure_id = form2.procedure_id.data
    a = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,

    ).first()
    a.outmiles = outmiles
    a.actual_start_datetime = datetime.now()
    db.session.add(a)
    try:
        db.session.commit()
        flash("您已确认车辆出厂，公里数提交成功")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("404.html")

    pagination = CarProcedureInfo.query.filter(
        # CarProcedureInfo.approval_time.contains(keywords),
        CarProcedureInfo.status2 == 1,
        CarProcedureInfo.company == current_user.company,
        CarProcedureInfo.actual_end_datetime == None,

    ).order_by(
        CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    my_procedure = pagination.items

    return render_template("home/confirmcar.html", my_procedure=my_procedure, pagination=pagination, form=form,
                           form2=form2)


# 确认快递邮寄出厂流程操作界面
@home.route("/confirmpackage", methods=["GET", "POST"])
@login_required
@permission_required(Permission.CONFIRM)
def confirmpackage():
    page = request.args.get("page", 1, type=int)
    pagination = PackageProcedureInfo.query.filter(
        PackageProcedureInfo.status == "待寄出"

    ).order_by(
        PackageProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    my_procedure = pagination.items
    return render_template("home/confirmpackage.html", my_procedure=my_procedure, pagination=pagination)


# 确认车辆出厂
@home.route("/confirmleave/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.CONFIRM)
def confirmleave(procedure_id):
    a = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()

    a.actual_start_datetime = datetime.now()
    db.session.add(a)
    try:
        db.session.commit()
        flash("您已确认车辆出厂")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("404.html")

    return redirect(url_for("home.confirmcar"))


# 确认车辆入厂
@home.route("/confirmarrive/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.CONFIRM)
def confirmarrive(procedure_id):
    form = MilesForm()
    miles = form.miles.data
    a = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    a.miles = miles

    db.session.add(a)
    try:
        db.session.commit()
        return redirect(url_for("home.success"))
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("404.html")

    return redirect(url_for("home.confirmcar"))


# # 提示响应成功地址
# @home.route('/success')
# @login_required
# def success():
#     resp = make_response(redirect(url_for('.confirmleave')))
#     resp.
#     return resp(200)

# @home.before_request
# def homeg():
#     g.ifok = "kong"


# 确认快递已经邮寄出
@home.route("/confircollect/<procedure_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.CONFIRM)
def confircollect(procedure_id):
    a = PackageProcedureInfo.query.filter(
        PackageProcedureInfo.id == procedure_id,
    ).first()

    a.status = "已寄出"
    a.confirm_time = datetime.now()
    db.session.add(a)
    try:
        db.session.commit()
        flash("快递已经确认从公司邮寄出厂")
    except:
        db.session.rollback()
        flash("提交数据失败")
        return render_template("404.html")

    return redirect(url_for("home.confirmpackage"))


# 作废流程页
@home.route("/rejectedprocedure", methods=["GET", "POST"])
@login_required
@permission_required(Permission.APPLY)
def rejectedprocedure():
    page = request.args.get("page", 1, type=int)
    keywords = request.args.get("keywords", "")

    pagination = CarProcedureInfo.query.filter(
        CarProcedureInfo.approval_time.contains(keywords),
        or_(
            CarProcedureInfo.status1 == 2,
            CarProcedureInfo.status2 == 2,
        ),
        or_(CarProcedureInfo.user_id == current_user.id,
            CarProcedureInfo.first_approval == current_user.id,
            CarProcedureInfo.second_approval == current_user.id
            ),
        CarProcedureInfo.company == current_user.company,

    ).order_by(
        CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
    ["FLASKY_PER_PAGE"], error_out=False)
    my_procedure = pagination.items

    return render_template("home/rejectedprocedure.html", my_procedure=my_procedure, pagination=pagination)


# # 所有流程清导出界面单页
# @home.route("/procedurelists", methods=["GET", "POST"])
# @login_required
# @permission_required(Permission.L2_APPROVAL)
# def procedurelists():
#     if request.method == "POST":
#         year = request.form.get("year")
#         month = request.form.get("month")
#         arrays = CarProcedureInfo.query.filter(
#             extract("year", CarProcedureInfo.actual_end_datetime) == year,
#             extract("month", CarProcedureInfo.actual_end_datetime) == month
#
#         ).order_by(
#             CarProcedureInfo.actual_end_datetime.asc()).all()
#         if arrays:  # 如果有数据则导出
#             column = [["序号", "流程编号", "结束日期", "申请人", "目的地", "用车原因", "车型", "是否用ETC", "公里数"]]
#             i = 1
#             for array in arrays:
#                 list = array.jsonstr()  # 将每一行查询的数据转换成字典格式
#                 array_content = [i,
#                                  list["id"],
#                                  list["actual_end_datetime"][0:10],
#                                  list["user_name"],
#                                  list["arrival_place"],
#                                  list["reason"],
#                                  list["car_name"],
#                                  list["etc"],
#                                  ]  # 将每一行的数据需要的先转换成字典，然后把相应内容导出。
#                 column.append(array_content)
#                 i += 1
#                 filename = "用车情况按月统计表" + datetime.now().__str__()[0:10]
#
#             return excel.make_response_from_array(column, file_type="xls", file_name=filename)
#         else:
#             flash("该月份没有用车记录")
#             return redirect(url_for("home.procedurelists"))
#     if request.method == "GET":
#         page = request.args.get("page", 1, type=int)
#         keywords = request.args.get("keywords", "")
#
#         pagination = CarProcedureInfo.query.filter(CarProcedureInfo.user_id == current_user.id,
#                                                    CarProcedureInfo.approval_time.contains(keywords),
#                                                    ).order_by(
#             CarProcedureInfo.approval_time.desc()).paginate(page, per_page=current_app.config
#         ["FLASKY_PER_PAGE"], error_out=False)
#         my_procedure = pagination.items
#     return render_template("home/procedurelists.html", my_procedure=my_procedure, pagination=pagination)

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
                 "运单号", "付款方式", "寄件人", "寄件部门", "确认邮寄/收货时间"]]
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


# # 所有流程清导出界面单页
# @home.route("/procedurelists", methods=["GET", "POST"])
# @login_required
# @permission_required(Permission.L2_APPROVAL)
# def procedurelists():
#     if request.method == "GET":
#         return render_template("home/procedurelists.html")
#     else:
#         data1 = json.loads(request.get_data())
#         year = data1["year"]
#         month = data1["month"]
#         arrays = CarProcedureInfo.query.filter(
#             extract("year", CarProcedureInfo.actual_end_datetime) == year,
#             extract("month", CarProcedureInfo.actual_end_datetime) == month
#
#         ).order_by(
#             CarProcedureInfo.actual_end_datetime.asc()).all()
#         if arrays:  # 如果有数据则导出
#             column = [["序号", "流程编号", "结束日期", "申请人", "目的地", "用车原因", "车型", "是否用ETC", "公里数"]]
#             i = 1
#             for array in arrays:
#                 list = array.jsonstr()  # 将每一行查询的数据转换成字典格式
#                 array_content = [i,
#                                  list["id"],
#                                  list["actual_end_datetime"][0:10],
#                                  list["user_name"],
#                                  list["arrival_place"],
#                                  list["reason"],
#                                  list["car_name"],
#                                  list["etc"],
#                                  ]  # 将每一行的数据需要的先转换成字典，然后把相应内容导出。
#                 column.append(array_content)
#                 i += 1
#                 filename = "用车情况按月统计表" + datetime.now().__str__()[0:10]
#             return excel.make_response_from_array(column, file_type="xls", file_name=filename)
#         else:
#             flash("该月份没有用车记录")
#             return redirect("home/procedurelists.html")


# 使用openpyxl导出方法，这个可以通过openpyxl对单元格的内容进行操作。
# if request.method == "POST":
#        year = request.form.get("year")
#        month = request.form.get("month")
#        query_sets = CarProcedureInfo.query.filter(
#            extract("year", CarProcedureInfo.actual_end_datetime) == year,
#            extract("month", CarProcedureInfo.actual_end_datetime) == month
#
#        ).order_by(
#            CarProcedureInfo.actual_end_datetime.asc()).all()
#        wb = Workbook()
#        wb.create_sheet("用车信息")
#        ws = wb.active
#        ws["A4"] = 4
#        ws["A1"]="nihao "
#
#        content = save_virtual_workbook(wb)  # 此处这个save_virtual_workbook函数将 Excel 文档写入到内存，返回一个字节数组。
#
#        resp = make_response(content)
#        resp.headers["Content-Disposition"] = 'attachment; filename=carinfos.xlsx'
#        resp.headers['Content-Type'] = 'application/x-xlsx'
#        return resp


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
    # if request.method == "GET":
        form = AddNewUserForm()
        form.department.choices = [(c.id, c.department) for c in
                                   CompanyDepartment.query.filter_by(company=current_user.company)]
        page = request.args.get("page", 1, type=int)
        keywords = request.args.get("keywords", "")
        pagination = User.query.filter(User.username.contains(keywords),
                                       User.status == "正常",
                                       User.company == current_user.company,
                                       ).order_by(
            User.id.desc()).paginate(page, per_page=current_app.config
        ["FLASKY_PER_PAGE"], error_out=False)
        users = pagination.items
        # 获取部门的id并找到部门名称
        departmentid = request.form.get("department")
        departments = CompanyDepartment.query.filter_by(id=departmentid).first()
        department = departments.department
        if form.validate_on_submit():

            newuser = User(username=form.name.data,
                           department=department,
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
        return render_template("home/usermanage.html", users=users, pagination=pagination, form=form)
    # if request.method == "Post":
    #     form = AddNewUserForm()
    #     name = form.name.data
    #     if not name:
    #         flash("姓名不能为空，请重新提交")
    #     if form.validate_on_submit():
    #
    #         department = request.form.get("department")
    #         newuser = User(username=form.name.data,
    #                        department=department,
    #                        role_id=form.roleid.data,
    #                        tel=form.tel.data,
    #                        password="123456",
    #                        status="正常",
    #                        company=current_user.company
    #                        )
    #
    #         db.session.add(newuser)
    #         try:
    #             db.session.commit()
    #             flash("您已添加新员工{0}，密码为123456".format(name))
    #         except:
    #             db.session.rollback()
    #             flash("用户已存在，添加失败")
    #             return render_template("404.html")
    #     return redirect(url_for("home.usermanage"))


# 对删除的用户进行标记
@home.route("/deluser/<user_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def deluser(user_id):
    # 根据流程id找到该条记录
    user = User.query.filter(
        User.id == user_id,
    ).first()
    # 对该条记录的status1进行更新
    user.status = "删除"
    db.session.add(user)
    name = user.username
    try:
        db.session.commit()
        flash("你已删除{0}员工".format(name))
    except:
        db.session.rollback()
        flash("删除失败")
        return render_template("404.html")

    return redirect(url_for("home.usermanage"))


# 重置用户密码
@home.route("/resetcode/<user_id>", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def resetcode(user_id):
    # 根据流程id找到该条记录
    user = User.query.filter(
        User.id == user_id,
    ).first()
    # 对该条记录的status1进行更新
    user.password = "123456"
    db.session.add(user)
    name = user.username
    try:
        db.session.commit()
        flash("你已重置员工{0}密码为123456".format(name))
    except:
        db.session.rollback()
        flash("重置失败")
        return render_template("404.html")

    return redirect(url_for("home.usermanage"))


# 添加新用户
@home.route("/addnewuser", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def addnewuser():
    form = AddNewUserForm()
    name = form.name.data
    if not name:
        flash("姓名不能为空，请重新提交")
    if form.validate_on_submit():

        department = request.form.get("department")
        newuser = User(username=form.name.data,
                       department=department,
                       role_id=form.roleid.data,
                       tel=form.tel.data,
                       password="123456",
                       status="正常",
                       company=current_user.company
                       )

        db.session.add(newuser)
        try:
            db.session.commit()
            flash("您已添加新员工{0}，密码为123456".format(name))
        except:
            db.session.rollback()
            flash("用户已存在，添加失败")
            return render_template("404.html")

    return redirect(url_for("home.usermanage"))


# 修改用户信息
@home.route("/alterusersubmit", methods=["GET", "POST"])
@login_required
@permission_required(Permission.L2_APPROVAL)
def alterusersubmit():
    user_id = request.form.get("user_id")
    name = request.form.get("altername")
    department = request.form.get("alterdepartment")
    tel = request.form.get("altertel")
    role_id = request.form.get("alterroleid")
    # 根据流程id找到该条记录
    user = User.query.filter(
        User.id == user_id,
    ).first()
    # 对该条记录的status1进行更新
    user.username = name
    user.department = department
    user.tel = tel
    user.role_id = role_id
    db.session.add(user)
    name = user.username
    try:
        db.session.commit()
        flash("你已修改员工{0}的信息".format(name))
    except:
        db.session.rollback()
        flash("修改信息失败")
        return render_template("404.html")

    return redirect(url_for("home.usermanage"))


# 查询详情页
@home.route("/procedureinfos", methods=["POST"])
@login_required
def procedureinfos():
    data1 = json.loads(request.get_data())
    procedure_id = data1["procedure_id"]
    procedureinfos = CarProcedureInfo.query.filter(
        CarProcedureInfo.id == procedure_id,
    ).first()
    data = procedureinfos.jsonstr()
    return jsonify(data)


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
