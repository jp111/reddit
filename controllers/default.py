# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

#########################################################################
## This is a sample controller
## - index is the default action of any application
## - user is required for authentication and authorization
## - download is for downloading files uploaded in the db (does streaming)
## - call exposes all registered services (none by default)
#########################################################################


def index():
	form=db(db.categories.id>0).select()
	return dict(form=form)
#	if request.args == "me":
#		response.flash= 'Sorry, no news found'
	"""
	example action using the internationalization operator T and flash
	rendered by views/default/index.html or views/generic.html

	if you need a simple wiki simple replace the two lines below with:
	return auth.wiki()
	"""
	response.flash = T("Welcome to web2py!")
	return dict(message=T('Hello World'))


def user():
	"""
	exposes:
	http://..../[app]/default/user/login
	http://..../[app]/default/user/logout
	http://..../[app]/default/user/register
	http://..../[app]/default/user/profile
	http://..../[app]/default/user/retrieve_password
	http://..../[app]/default/user/change_password
	http://..../[app]/default/user/manage_users (requires membership in 
	use @auth.requires_login()
		@auth.requires_membership('group name')
		@auth.requires_permission('read','table name',record_id)
	to decorate functions that need access control
	"""
	return dict(form=auth())

@cache.action()
def download():
	"""
	allows downloading of uploaded files
	http://..../[app]/default/download/[filename]
	"""
	return response.download(request, db)


def call():
	"""
	exposes services. for example:
	http://..../[app]/default/call/jsonrpc
	decorate with @services.jsonrpc the functions to expose
	supports xml, json, xmlrpc, jsonrpc, amfrpc, rss, csv
	"""
	return service()


@auth.requires_signature()
def data():
	"""
	http://..../[app]/default/data/tables
	http://..../[app]/default/data/create/[table]
	http://..../[app]/default/data/read/[table]/[id]
	http://..../[app]/default/data/update/[table]/[id]
	http://..../[app]/default/data/delete/[table]/[id]
	http://..../[app]/default/data/select/[table]
	http://..../[app]/default/data/search/[table]
	but URLs must be signed, i.e. linked with
	  A('table',_href=URL('data/tables',user_signature=True))
	or with the signed load operator
	  LOAD('default','data.load',args='tables',ajax=True,user_signature=True)
	"""
	return dict(form=crud())

#my functions
@auth.requires_login()
def add_category():
	form=SQLFORM(db.categories)
	if form.process().accepted:
		response.flash = 'category added'

	return dict(form=form)
@auth.requires_login()
def add_item():
	form=SQLFORM(db.item)
	if form.process().accepted:
		response.flash = 'item added'
		new_item=db(db.item.id>0).select().last()
		new_item.userid=auth.user.id
		new_item.update_record()
	return dict(form=form)

def category_page():
	#	print request.args
	item=db(db.item.category == request.args(0,cast=int)).select(db.item.ALL,orderby=~db.item.totalp)
	return dict(item=item)

def nonews():
	return dict()
@auth.requires_login()
def respy():
	var=request.args(1,cast=int)
	hitem=db(db.item.id == request.args(0,cast=int)).select().last()
	exist=db((db.mylike.userid==auth.user.id) & (db.mylike.itemid==hitem.id) ).select()
	if(len(exist)==0):
		db.mylike.insert(status=var,itemid=hitem.id,userid=auth.user.id)
		if var==1:
			session.flash = 'item liked'
			hitem.totalp += 5
		else:
			session.flash = 'item disliked'
			hitem.totalp -= 3
		hitem.update_record()
		cat=db(db.categories.id==hitem.category).select()
		redirect(URL('category_page',args=cat[0].id))

	else:
		if var==1:

			if exist[0].status==-1:
				session.flash = 'item liked'
				hitem.totalp += 8
			if exist[0].status==0:
				session.flash = 'item liked'
				hitem.totalp += 5

		elif var==-1:
			if exist[0].status==1:
				session.flash = 'item disliked'
				hitem.totalp -= 8
			if exist[0].status==0:
				session.flash = 'item disliked'
				hitem.totalp -= 3
		elif var==0:
			if exist[0].status==1:
				session.flash = 'item not liked anymore '
				hitem.totalp -=5
			if exist[0].status==-1:
				session.flash = 'item not disliked anymore '
				hitem.totalp +=3


		exist[0].status=var
		exist[0].update_record()
		hitem.update_record()
		cat=db(db.categories.id==hitem.category).select()
		redirect(URL('category_page',args=cat[0].id))
	return dict()

@auth.requires_login()
def edit():
	item=db(db.item.id==request.args(0,cast=int)).select().last()
	print item['category']
	form=SQLFORM.factory(
			Field('userid','integer',readable=False,writable=False),
			Field('category','string',requires=IS_IN_DB(db,'categories.id','categories.category'),default=item.category),
			Field('heading','string',default=item.heading),
			Field('url','string',requires=IS_URL(),default=item.url),
			Field('totalp','integer',default=100,writable=False,readable=False)
			)
	if form.process().accepted:
		session.flash = 'News item updated successfully'
		db(db.item.id==request.args(0,cast=int)).update(category=form.vars.category,heading=form.vars.heading,url=form.vars.url)
		hitem=db(db.item.id == request.args(0,cast=int)).select().last()
		cat=db(db.categories.id==hitem.category).select()
		redirect(URL('category_page',args=cat[0].id))
	return dict(form=form)

@auth.requires_login()
def comment():
	form=SQLFORM.factory(Field('come','string',label="What's your comment"))
	if form.process().accepted:
		session.flash = 'comment added'
#		last_comment=db(db.comments.id>0).select().last()
#		last_comment.userid=auth.user.id
		po=request.args(0,cast=int)
		print auth.user.id
		print po
		db.comments.insert(userid=auth.user.id,itemid=po,item_comment=form.vars.come,time_change=request.now)
		#db.comments.update_record()
	return dict(form=form)

@auth.requires_login()
def delete_item():
	k=request.args(0,cast=int)
	form=db(db.item.id == k).select()
	a=form[0]['category']
	session.flash = 'news item deleted'
	form=db(db.item.id == k).delete()
	redirect(URL('category_page',args=a))
	return dict()

@auth.requires_login()
def delete_user():
	form = db(db.auth_user.id>0).select()
#	print form[0]['first_name']
	return dict(form=form)

@auth.requires_login()
def delete_given():
	k=request.args(0,cast=int)
	form=db(db.auth_user.id == k).select()
	#print form[0]
	a=form[0]['id']
#	print a
	session.flash = 'user deleted'
	like=db(form[0]['id'] == db.mylike.userid).select()
	print like
	for some in like:
		item=db(db.item.id == some.itemid).select()
		print item
		var=some.status
		if var == -1:
			item[0].totalp +=3
		elif var == 1:
			item[0].totalp -=5
		item[0].update_record()
#	item=db(like[0]['id'] == db.item.userid).select()
#	print item
#	print item.totalp
	form=db(db.auth_user.id == k).delete()
	redirect(URL('delete_user',args=a))
