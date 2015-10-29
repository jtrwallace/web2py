# -*- coding: utf-8 -*-
# this file is released under public domain and you can use without limitations

from datetime import datetime, timedelta
import calendar

def index():
    redirect(URL('default', 'boards'))
    return 0

def boards():
    boards = db().select(db.boards.ALL, orderby=~db.boards.board_last_updated)
    for board in boards:
        board['board_pretty_updated'] = pretty_date(board['board_last_updated'])
        board['total_count'] = len(db(db.posts.board_id == board.id).select())
        board['new_today'] = len(db((db.posts.board_id == board.id) & (db.posts.posting_time >= (datetime.utcnow() - timedelta(days=1)))).select())
    return dict(boards=boards)

def board():
    board = db.boards(request.args(0))
    posts = db(db.posts.board_id == board.id).select(orderby=~db.posts.posting_time)
    for post in posts:
        post['posting_time_pretty'] = pretty_date(post['posting_time'])
    return dict(board=board, posts=posts)

def create_board():
    db.boards.board_author.readable = db.boards.board_author.writable = False
    db.boards.board_last_updated.readable = db.boards.board_last_updated.writable = False
    db.boards.board_pretty_updated.readable = db.boards.board_pretty_updated.writable = False
    form=SQLFORM(db.boards)
    if form.process().accepted:
        redirect(URL('default', 'boards'))
    return dict(form=form)

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

def pretty_date(date):
    month_abr = calendar.month_abbr[date.month]
    pretty = month_abr + " " + str(date.day) + ", " + str(date.year) + " " + str(date.time())
    return pretty

def user():
    #redirect('default', 'board', args=request.args(1))
    return dict(form=auth())


@cache.action()
def download():
    return response.download(request, db)


def call():
    return service()


