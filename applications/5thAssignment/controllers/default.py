# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

from datetime import datetime, timedelta
from gluon import utils as gluon_utils
import json
import calendar

def index():
    redirect(URL('default', 'boards'))
    return 0

def boards():
    return dict()

def load_boards():
    #Want to serve up all completed boards as well as all drafts that belong only to the user.
    not_draft_boards_query = (db.boards.is_draft == False)
    my_drafts_boards_query = (db.boards.board_author == auth.user_id) & (db.boards.is_draft == True)
    not_drafts = db(not_draft_boards_query)
    my_drafts = db(my_drafts_boards_query)
    all_boards = not_drafts.select() & my_drafts.select()
    for board in all_boards:
        board['total_count'] = len(db(db.posts.board_id == board.id).select())
        board['new_today'] = len(db((db.posts.board_id == board.id) & (db.posts.posting_time >= (datetime.utcnow() - timedelta(days=1)))).select())
    return response.json(list(all_boards))

def board():
    return dict(board_id=request.args(0))

def load_posts():
    board = db(db.boards.board_id == request.vars.board_id).select().first()
    posts = db(db.posts.board_id == board.id).select(orderby=~db.posts.posting_time)
    for post in posts:
        post['posting_time_pretty'] = pretty_date(post['posting_time'])
    return response.json(list(posts), list(board))

@auth.requires_signature()
def add_board():
    db.boards.update_or_insert((db.boards.board_id == request.vars.board_id),
            board_id=request.vars.board_id,
            board_name=request.vars.board_name,
            board_description=request.vars.board_description,
            is_draft=json.loads(request.vars.is_draft),
            active_draft_description=request.vars.active_draft_description,
            active_draft_name=request.vars.active_draft_name,
            board_last_updated=request.vars.board_last_updated,
            board_pretty_updated=request.vars.board_pretty_updated
            )
    return "ok"

@auth.requires_signature()
def del_board():
    db(db.boards.board_id == request.vars.board_id).delete()
    return "ok"

def create_post():
    board = db.boards(request.args(0))
    db.posts.posting_time.readable = db.posts.posting_time.writable = False
    db.posts.post_author.readable = db.posts.post_author.writable = False
    db.posts.board_id.readable = db.posts.board_id.writable = False
    db.posts.posting_time_pretty.readable = db.posts.posting_time_pretty.writable = False
    form=SQLFORM(db.posts)
    form.vars.board_id = board.id
    if form.process().accepted:
        board.board_last_updated = datetime.utcnow()
        board.update_record()
        try:
            db.commit()
        except Exception , e:
            logger.warning("Transaction commit failed while updating board time")
            redirect(URL('default', 'create_post', args=board.id))
        redirect(URL('default', 'board', args=board.id))
    return dict(form=form, board=board)

@auth.requires_signature()
def edit_post():
    post = db.posts(request.args(0))
    board = post.board_id
    db.posts.posting_time.readable = db.posts.posting_time.writable = False
    db.posts.post_author.readable = db.posts.post_author.writable = False
    db.posts.board_id.readable = db.posts.board_id.writable = False
    db.posts.posting_time_pretty.readable = db.posts.posting_time_pretty.writable = False
    db.posts.id.readable = db.posts.id.writable = False
    form=SQLFORM(db.posts, post)
    if form.process().accepted:
        board.board_last_updated = datetime.utcnow()
        board.update_record()
        try:
            db.commit()
        except Exception , e:
            logger.warning("Transaction commit failed while updating board time")
            redirect(URL('default', 'edit_post', args=[post.id, board.id]))
        redirect(URL('default', 'board', args=board.id))
    return dict(board=board, form=form)

@auth.requires_signature()
def delete_post():
    post = db.posts(request.args(0))
    board = post.board_id
    db(db.posts.id == post.id).delete()
    redirect(URL('default', 'board', args=board.id))
    return 0

def date():
    date = datetime.utcnow()
    return response.json(date);

def pretty_date():
    date = datetime.utcnow()
    month_abr = calendar.month_abbr[date.month]
    pretty = month_abr + " " + str(date.day) + " " + str(date.time().strftime("%H:%M"))
    return response.json(pretty);

def pretty_date(date):
    month_abr = calendar.month_abbr[date.month]
    pretty = month_abr + " " + str(date.day) + " " + str(date.time().strftime("%H:%M"))
    return pretty

def user():
    return dict(form=auth())


@cache.action()
def download():
    return response.download(request, db)


def call():
    return service()


