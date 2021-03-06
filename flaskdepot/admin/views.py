import os
from flask import Blueprint, abort, flash, render_template, current_app, request, url_for
from flask.ext.login import login_required, current_user
from slugify import slugify
from sqlalchemy import func
from werkzeug.exceptions import BadRequest
from werkzeug.utils import secure_filename, redirect
from flaskdepot.admin.controllers import AdminAccountEditForm, AdminFileEditForm, AdminAddCategoryForm, \
    AdminRenameCategoryForm, AdminDescribeCategoryForm, AdminAddUsergroupForm, AdminRenameUsergroupForm
from flaskdepot.extensions import db
from flaskdepot.file.models import Download, File, Vote, Comment, BroadCategory, NarrowCategory
from flaskdepot.user.models import User, Usergroup
from flaskdepot.utils.helper import likeable

admin = Blueprint("admin", __name__)


@admin.before_request
def check_admin():
    if not current_user.group.is_admin:
        abort(403)


@admin.route('/index', methods=['GET'])
@login_required
def index():
    stats = list()
    stats.append({
        'name': 'Downloads',
        'result': db.session.query(func.count(Download.id)).scalar()
    })
    stats.append({
        'name': 'Files',
        'result': db.session.query(func.count(File.id)).scalar()
    })
    stats.append({
        'name': 'Users',
        'result': db.session.query(func.count(User.id)).scalar()
    })
    stats.append({
        'name': 'Votes',
        'result': db.session.query(func.count(Vote.id)).scalar()
    })
    stats.append({
        'name': 'Comments',
        'result': db.session.query(func.count(Comment.id)).scalar()
    })

    return render_template('admin/index.html', stats=stats, title="Administration")


@admin.route('/user', methods=['GET'])
@admin.route('/user/page-<int:page>', methods=['GET'])
@login_required
def user(page=1):
    users = User.query
    _username = request.args.get('username')
    _email = request.args.get('email')
    _usergroup = request.args.get('usergroup')

    if _username and len(_username) > 0:
        users = users.filter(User.username.ilike(likeable(_username)))
    if _email and len(_email) > 0:
        users = users.filter(User.email.ilike(likeable(_email)))
    if _usergroup and len(_usergroup) > 0:
        users = users.filter(User.group_id.is_(_usergroup))

    users = users.paginate(page, current_app.config['RESULTS_PER_PAGE'], False)
    usergroups = Usergroup.query.all()
    return render_template('admin/user.html', users=users, usergroups=usergroups, title="User administration")


@admin.route('/file', methods=['GET'])
@admin.route('/file/page-<int:page>', methods=['GET'])
@login_required
def file(page=1):
    files = File.query
    _filename = request.args.get('filename')
    _author = request.args.get('author')

    if _filename and len(_filename) > 0:
        files = files.filter(File.file_name.ilike(likeable(_filename)))
    if _author and len(_author) > 0:
        files = files.filter(File.author_id.is_(_author))

    files = files.paginate(page, current_app.config['RESULTS_PER_PAGE'], False)
    users = db.session.query(User)\
        .join(Usergroup)\
        .filter(Usergroup.is_uploader)\
        .filter(User.group_id == Usergroup.id)\
        .all()
    return render_template('admin/file.html', files=files, users=users, title="File administration")


@admin.route('/usergroup', methods=['GET', 'POST'])
@login_required
def usergroup():
    groups = Usergroup.query.all()
    form = AdminAddUsergroupForm()
    form.next.data = url_for('admin.usergroup')

    if form.validate_on_submit():
        group = Usergroup()
        group.name = form.name.data
        group.is_banned = form.is_banned.data
        group.is_default = form.is_default.data
        group.is_admin = form.is_admin.data
        group.is_uploader = form.is_uploader.data

        db.session.add(group)
        db.session.commit()
        flash('Usergroup has been added')

        return form.redirect()

    return render_template('admin/usergroup.html', groups=groups, form=form, title="Usergroup administration")


@admin.route('/usergroup/<groupid>/switch', methods=['GET'])
@login_required
def switch_usergroup(groupid):
    group = Usergroup.query.filter_by(id=groupid).first_or_404()
    _type = request.args.get('type')

    if _type == 'banned':
        group.is_banned = False if group.is_banned else True
    elif _type == 'default':
        group.is_default = False if group.is_default else True
    elif _type == 'admin':
        group.is_admin = False if group.is_admin else True
    elif _type == 'uploader':
        group.is_uploader = False if group.is_uploader else True
    else:
        raise BadRequest()

    db.session.commit()
    flash('Usergroup has been updated')

    return redirect(url_for('admin.usergroup'))


@admin.route('/usergroup/<groupid>/rename', methods=['GET', 'POST'])
@login_required
def rename_usergroup(groupid):
    group = Usergroup.query.filter_by(id=groupid).first_or_404()

    form = AdminRenameUsergroupForm()
    form.next.data = url_for('admin.usergroup')

    if request.method == 'GET':
        form.name.data = group.name

    if form.validate_on_submit():
        group.name = form.name.data

        db.session.commit()

        flash('Usergroup name has been updated')
        return form.redirect()

    return render_template('admin/usergroup_rename.html', form=form)


@admin.route('/usergroup/<groupid>/delete', methods=['GET'])
def delete_usergroup(groupid):
    group = Usergroup.query.filter_by(id=groupid).first_or_404()
    if group.users.count() > 0:
        raise BadRequest()
    else:
        db.session.delete(group)
        db.session.commit()

        flash('Usergroup has been removed')
        return redirect(url_for('admin.usergroup'))


@admin.route('/category', methods=['GET', 'POST'])
@login_required
def category():
    broad_categories = BroadCategory.query.all()
    narrow_categories = NarrowCategory.query.all()
    form = AdminAddCategoryForm()
    form.next.data = url_for('admin.category')

    if form.validate_on_submit():
        cat = None
        if form.type.data == 'broad':
            cat = BroadCategory()
        elif form.type.data == 'narrow':
            cat = NarrowCategory()
        else:
            raise BadRequest()
        cat.description = form.description.data if len(form.description.data) > 0 else None
        cat.name = form.name.data

        db.session.add(cat)
        db.session.commit()

        flash('Category has been added')
        return form.redirect()

    return render_template('admin/category.html',
                           broad=broad_categories,
                           narrow=narrow_categories,
                           form=form,
                           title="Category administration")


@admin.route('/category/delete', methods=['GET'])
@login_required
def delete_category():
    _type = request.args.get('type')
    _catid = request.args.get('catid')
    cat = None

    if _type == 'broad':
        cat = BroadCategory.query.filter_by(id=_catid).first_or_404()
    elif _type == 'narrow':
        cat = NarrowCategory.query.filter_by(id=_catid).first_or_404()
    else:
        raise BadRequest()

    if cat.files.count() > 0:
        raise BadRequest()

    db.session.delete(cat)
    db.session.commit()
    flash('Category has been deleted')
    return redirect(url_for('admin.category'))


@admin.route('/category/rename', methods=['GET', 'POST'])
@login_required
def rename_category():
    _type = request.args.get('type')
    _catid = request.args.get('catid')
    cat = None

    if _type == 'broad':
        cat = BroadCategory.query.filter_by(id=_catid).first_or_404()
    elif _type == 'narrow':
        cat = NarrowCategory.query.filter_by(id=_catid).first_or_404()
    else:
        raise BadRequest()

    form = AdminRenameCategoryForm()
    form.next.data = url_for('admin.category')

    if request.method == 'GET':
        form.type = _type
        form.catid = _catid
        form.name.data = cat.name

    if form.validate_on_submit():
        cat.name = form.name.data

        db.session.commit()
        flash('Category name has been updated')
        return form.redirect()

    return render_template('admin/category_rename.html', form=form)



@admin.route('/category/describe', methods=['GET', 'POST'])
def describe_category():
    _type = request.args.get('type')
    _catid = request.args.get('catid')
    cat = None

    if _type == 'broad':
        cat = BroadCategory.query.filter_by(id=_catid).first_or_404()
    elif _type == 'narrow':
        cat = NarrowCategory.query.filter_by(id=_catid).first_or_404()
    else:
        raise BadRequest()

    form = AdminDescribeCategoryForm()
    form.next.data = url_for('admin.category')

    if request.method == 'GET':
        form.type = _type
        form.catid = _catid
        form.description.data = cat.description if cat.description else ''

    if form.validate_on_submit():
        cat.description = form.description.data

        db.session.commit()
        flash('Category description has been updated')
        return form.redirect()

    return render_template('admin/category_describe.html', form=form)

@admin.route('/file/<fileid>/edit', methods=['GET', 'POST'])
@admin.route('/file/<fileid>/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit_file(fileid, slug=None):
    form = AdminFileEditForm()
    _file = File.query.filter_by(id=fileid).first_or_404()

    form.broad_category.choices = [(cat.id, cat.name) for cat in BroadCategory.query.order_by('name')]
    form.narrow_category.choices = [(cat.id, cat.name) for cat in NarrowCategory.query.order_by('name')]
    form.fileid = fileid

    if request.method == 'GET':
        form.filename.data = _file.name
        form.description.data = _file.description
        form.version.data = _file.version
        form.broad_category.data = _file.broad_category_id
        form.narrow_category.data = _file.narrow_category_id

    if form.validate_on_submit():
        _file.description = form.description.data
        _file.version = form.version.data
        _file.broad_category_id = form.broad_category.data
        _file.narrow_category_id = form.narrow_category.data

        file_subdir = os.path.join(current_app.config['FILE_DIR'], _file.slug)
        image_subdir = os.path.join(current_app.config['PREVIEW_DIR'], _file.slug)

        if slugify(form.filename.data) != _file.slug:
            new_file_subdir = os.path.join(current_app.config['FILE_DIR'], slugify(form.filename.data))
            new_image_subdir = os.path.join(current_app.config['PREVIEW_DIR'], slugify(form.filename.data))

            os.rename(file_subdir, new_file_subdir)
            os.rename(image_subdir, new_image_subdir)
            _file.name = form.filename.data
            _file.slug = slugify(_file.name)

            file_subdir = new_file_subdir
            image_subdir = new_image_subdir

        if len(form.package.data.filename) > 0:
            _file.file_name = secure_filename(form.package.data.filename)
            form.package.data.save(os.path.join(file_subdir, _file.file_name))
        if len(form.image_1.data.filename) > 0:
            _file.preview1_name = secure_filename(form.image_1.data.filename)
            form.image_1.data.save(os.path.join(image_subdir, _file.preview1_name))
        if len(form.image_2.data.filename) > 0:
            _file.preview2_name = secure_filename(form.image_2.data.filename)
            form.image_2.data.save(os.path.join(image_subdir, _file.preview2_name))

        db.session.commit()

        flash('File has been updated')
        return form.redirect(url_for('file.file_one', fileid=fileid, slug=_file.slug))

    return render_template('admin/file_edit.html', form=form, fileid=fileid, title="Edit file")


@admin.route('/user/<id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(id):
    _user = User.query.filter_by(id=id).first()
    form = AdminAccountEditForm()
    form.group.choices = [(group.id, group.name) for group in Usergroup.query.order_by('name')]

    if form.validate_on_submit():
        if form.group.data and form.group.data is not _user.group.id:
            _user.group_id = form.group.data
            flash('The user group has been updated')
        if form.username.data:
            _user.username = form.username.data
            flash('The username has been updated')
        db.session.commit()
    else:
        form.group.data = _user.group_id

    return render_template('admin/user_edit.html',
                           form=form,
                           title=u"Edit account for {0}".format(_user.username),
                           user=_user)