from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms.fields.simple import StringField, TextAreaField, PasswordField, EmailField
from wtforms.validators import DataRequired, Length, EqualTo, Email, Regexp

#회원 가입 폼
class UserCreateForm(FlaskForm):
    username = StringField('사용자이름',validators=[DataRequired(), Length(min=3, max=12,
           message='사용자이름은 3자에서 12자 사이여야 합니다.')])
    password1 = PasswordField('비밀번호',validators=[DataRequired(), EqualTo('password2', message='비밀번호가 일치하지 않습니다.')])
    password2 = PasswordField('비밀번호 확인',validators=[DataRequired()])
    email=EmailField('이메일', validators=[DataRequired(), Email(message='올바른 이메일 형식이 아닙니다.')])
    phone = StringField('전화번호', validators=[DataRequired(),
            Regexp(r'^\d{3}-\d{3,4}-\d{4}$', message="올바른 전화번호 형식이 아닙니다.")])

#로그인 폼
class UserLoginForm(FlaskForm):
    username=StringField('사용자이름', validators=[DataRequired(), Length(min=3, max=25)])
    password=PasswordField('비밀번호', validators=[DataRequired()])