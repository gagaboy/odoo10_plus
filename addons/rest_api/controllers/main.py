# Part of Flectra. See LICENSE file for full copyright and licensing details.

import functools
import hashlib
import logging
import os
from ast import literal_eval

try:
    import simplejson as json
except ImportError:
    import json
from base64 import b64encode
import werkzeug.wrappers

import flectra
from flectra import http
from flectra.http import request

_logger = logging.getLogger(__name__)


def get_fields_values_from_model(modelname, domain, offset=0, field=[],
                                 limit=None, order=None):
    Model = request.env[modelname]
    records = Model.search(domain, offset=offset, limit=limit, order=order)
    if not records:
        return {}
    result = []
    for record in records:
        result += [get_fields_values_from_one_record(record)]

    return result


def get_fields_values_from_one_record(record):
    result = {}
    for name, field in record._fields.items():
        if field.type == 'many2one' or field.type == 'reference':
            result[name] = {'id': record[name].id,
                            'name': record[name].name} if record[name] else None
        elif field.type == 'one2many' or field.type == 'many2many':
            result[name] = record[name].ids
            pass
        elif field.type == 'binary' and record[name]:
            base64_bytes = b64encode(record[name])
            result[name] = base64_bytes.decode('utf-8')
        else:
            result[name] = record[name] if record[name] else None

    return result


def convert_values_from_jdata_to_vals(modelname, jdata, creating=True):
    Model = request.env[modelname]
    x2m_fields = [f for f in jdata if type(jdata[f]) == list]
    f_props = Model.fields_get(x2m_fields)
    field_name = [name for name, field in Model._fields.items()]
    vals = {}
    for field in jdata:
        if field not in field_name:
            continue
        if field not in field_name:
            continue
        val = jdata[field]
        if type(val) != list:
            vals[field] = val
        else:
            # x2many
            #
            # Sample for One2many field:
            # 'bank_ids': [{'acc_number': '12345', 'bank_bic': '6789'},
            #  {'acc_number': '54321', 'bank_bic': '9876'}]
            vals[field] = []
            field_type = f_props[field]['type']
            # if updating of 'many2many'
            if (not creating) and (field_type == 'many2many'):
                # unlink all previous 'ids'
                vals[field].append((5,))

            for jrec in val:
                rec = {}
                for f in jrec:
                    rec[f] = jrec[f]
                if field_type == 'one2many':
                    if creating:
                        vals[field].append((0, 0, rec))
                    else:
                        if 'id' in rec:
                            id = rec['id']
                            del rec['id']
                            if len(rec):
                                # update record
                                vals[field].append((1, id, rec))
                            else:
                                # remove record
                                vals[field].append((2, id))
                        else:
                            # create record
                            vals[field].append((0, 0, rec))

                elif field_type == 'many2many':
                    # link current existing 'id'
                    vals[field].append((4, rec['id']))
    return vals


def create_object(modelname, vals):
    Model = request.env[modelname]
    return Model.create(vals)


def update_object(modelname, obj_id, vals):
    Model = request.env[modelname]
    record = Model.browse(obj_id)
    return record.write(vals)


def delete_object(modelname, obj_id):
    Model = request.env[modelname]
    record = Model.browse(obj_id)
    return record.unlink()


def wrap__resource__read_all(modelname, default_domain, success_code,
                             post={}):
    # Try convert http data into json:
    jdata = post
    # Default filter
    domain = default_domain or []
    field = []
    # Get additional parameters
    if 'filters' in jdata:
        domain += literal_eval(jdata['filters'])
    if 'field' in jdata:
        field += literal_eval(jdata['field'])
    if 'offset' in jdata:
        offset = int(jdata['offset'])
    else:
        offset = 0
    if 'limit' in jdata:
        limit = int(jdata['limit'])
    else:
        limit = None
    if 'order' in jdata:
        order = jdata['order']
    else:
        order = None
    # Reading object's data:
    Objects_Data = get_fields_values_from_model(
        modelname=modelname,
        domain=domain,
        offset=offset,
        limit=limit,
        order=order,
        field=field,
    )
    return successful_response(status=success_code,
                               dict_data={
                                   'count': len(Objects_Data),
                                   'results': Objects_Data
                               })


def wrap__resource__read_one(modelname, id, success_code):
    # Default search field
    try:
        id = int(id)
    except:
        pass

    if not id:
        return error_response_400__invalid_object_id()
    # Reading object's data:
    Object_Data = get_fields_values_from_model(modelname=modelname,
                                               domain=[('id', '=', id)])
    if Object_Data:
        return successful_response(success_code, Object_Data[0])
    else:
        return error_response_404__not_found_object_in_flectra()


def wrap__resource__create_one(modelname, default_vals, success_code):
    # Convert http data into json:
    rdata = request.httprequest.stream.read().decode('utf-8')
    jdata = json.loads(rdata)
    # Convert json data into flectra vals:
    vals = convert_values_from_jdata_to_vals(modelname, jdata)
    # Set default fields:
    if default_vals:
        vals.update(default_vals)
    # Try create new object
    try:
        new_id = create_object(modelname, vals)
        flectra_error = ''
    except Exception as e:
        new_id = None
        flectra_error = e.message
    if new_id:
        return successful_response(success_code, {'id': new_id.id})
    else:
        return error_response_409__not_created_object_in_flectra(flectra_error)


def wrap__resource__update_one(modelname, id, success_code):
    # Сheck id
    obj_id = None
    try:
        obj_id = int(id)
    except:
        pass
    if not obj_id:
        return error_response_400__invalid_object_id()
    # Convert http data into json:
    rdata = request.httprequest.stream.read().decode('utf-8')
    jdata = json.loads(rdata)
    # Convert json data into flectra vals:
    vals = convert_values_from_jdata_to_vals(modelname, jdata,creating=False)
    # Try update the object
    try:
        res = update_object(modelname, obj_id, vals)
        flectra_error = ''
    except Exception as e:
        res = None
        flectra_error = e.message
    if res:
        return successful_response(success_code, 'Record Updated '
                                                 'successfully!')
    else:
        return error_response_409__not_updated_object_in_flectra(flectra_error)


def wrap__resource__delete_one(modelname, id, success_code):
    # Сheck id
    obj_id = None
    try:
        obj_id = int(id)
    except:
        pass
    if not obj_id:
        return error_response_400__invalid_object_id()
    # Try delete the object
    try:
        res = delete_object(modelname, obj_id)
        flectra_error = ''
    except Exception as e:
        res = None
        flectra_error = e
    if res:
        return successful_response(success_code, 'Record Successfully '
                                                 'Deleted!')
    else:
        return error_response_409__not_deleted_object_in_flectra(flectra_error)


def check_permissions(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        _logger.info("Check permissions...")

        # Get access token from http header
        access_token = request.httprequest.headers.get('access_token')
        if not access_token:
            error_descrip = "No access token was provided in request header!"
            error = 'no_access_token'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        # Validate access token
        access_token_data = request.env['oauth.access_token'].sudo().search(
            [('token', '=', access_token)], order='id DESC', limit=1)

        if access_token_data._get_access_token(user_id=access_token_data.user_id.id) != access_token:
            return error_response_401__invalid_token()

        # Set session UID from current access token
        request.session.uid = access_token_data.user_id.id
        request.uid = access_token_data.user_id.id
        # The code, following the decorator
        return func(self, *args, **kwargs)

    return wrapper


def successful_response(status, dict_data):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        # headers = None,
        response=json.dumps(dict_data),
    )


def error_response(status, error, error_descrip):
    return werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        # headers = None,
        response=json.dumps({
            'error': error,
            'error_descrip': error_descrip,
        }),
    )


def error_response_400__invalid_object_id():
    error_descrip = "Invalid object 'id'!"
    error = 'invalid_object_id'
    _logger.error(error_descrip)
    return error_response(400, error, error_descrip)


def error_response_401__invalid_token():
    error_descrip = "Token is expired or invalid!"
    error = 'invalid_token'
    _logger.error(error_descrip)
    return error_response(401, error, error_descrip)


def error_response_404__not_found_object_in_flectra():
    error_descrip = "Not found object(s) in flectra!"
    error = 'not_found_object_in_flectra'
    _logger.error(error_descrip)
    return error_response(404, error, error_descrip)


def error_response_404_unable_delete_flectra():
    error_descrip = "Access Denied!"
    error = "you don't have access to delete records for this model"
    _logger.error(error_descrip)
    return error_response(404, error, error_descrip)


def error_response_409__not_created_object_in_flectra(flectra_error):
    error_descrip = "Not created object in flectra! ERROR: %s" % flectra_error
    error = 'not_created_object_in_flectra'
    _logger.error(error_descrip)
    return error_response(409, error, error_descrip)


def error_response_409__not_updated_object_in_flectra(flectra_error):
    error_descrip = "Not updated object in flectra! ERROR: %s" % flectra_error
    error = 'not_updated_object_in_flectra'
    _logger.error(error_descrip)
    return error_response(409, error, error_descrip)


def error_response_409__not_deleted_object_in_flectra(flectra_error):
    error_descrip = "Not deleted object in flectra! ERROR: %s" % flectra_error
    error = 'not_deleted_object_in_flectra'
    _logger.error(error_descrip)
    return error_response(409, error, error_descrip)


def generate_token(length=40):
    random_data = os.urandom(100)
    hash_gen = hashlib.new('sha512')
    hash_gen.update(random_data)
    return hash_gen.hexdigest()[:length]


# Read OAuth2 constants and setup token store:
db_name = flectra.tools.config.get('db_name')
if not db_name:
    _logger.error("ERROR: To proper setup OAuth - it's necessary to "
                  "set the parameter 'db_name' in flectra config file!")


# List of REST resources in current file:
#   (url prefix)            (method)     (action)
# /api/auth/get_tokens        POST    - Login in flectra and get access tokens
# /api/auth/delete_tokens     POST    - Delete access tokens from token store


# HTTP controller of REST resources:

class ControllerREST(http.Controller):

    # Login in flectra database and get access tokens:
    @http.route('/api/auth/get_tokens', methods=['POST'], type='http',
                auth='none', csrf=False)
    def api_auth_gettokens(self, **post):
        # Convert http data into json:
        db = post['db']
        username = post['username']
        password = post['password']
        # Compare dbname (from HTTP-request vs. flectra config):
        if db and (db != db_name):
            error_descrip = "Wrong 'dbname'!"
            error = 'wrong_dbname'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        # Empty 'db' or 'username' or 'password:
        if not db or not username or not password:
            error_descrip = "Empty value of 'db' or 'username' or 'password'!"
            error = 'empty_db_or_username_or_password'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        # Login in flectra database:
        try:
            request.session.authenticate(db, username, password)
        except:
            # Invalid database:
            error_descrip = "Invalid database!"
            error = 'invalid_database'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        uid = request.session.uid
        # flectra login failed:
        if not uid:
            error_descrip = "flectra User authentication failed!"
            error = 'flectra_user_authentication_failed'
            _logger.error(error_descrip)
            return error_response(401, error, error_descrip)

        # Generate tokens
        access_token = request.env['oauth.access_token']._get_access_token(user_id = uid, create = True)

        # Save all tokens in store
        _logger.info("Save OAuth2 tokens of user in store...")

        # Successful response:
        return werkzeug.wrappers.Response(
            status=200,
            content_type='application/json; charset=utf-8',
            headers=[('Cache-Control', 'no-store'),
                     ('Pragma', 'no-cache')],
            response=json.dumps({
                'uid': uid,
                'user_context': request.session.get_context() if uid else {},
                'company_id': request.env.user.company_id.id if uid else 'null',
                'access_token': access_token,
                'expires_in': request.env.ref('rest_api.oauth2_access_token_expires_in').sudo().value,
                }),
        )

    # Delete access tokens from token store:
    @http.route('/api/auth/delete_tokens', methods=['POST'], type='http',
                auth='none', csrf=False)
    def api_auth_deletetokens(self, **post):
        # Try convert http data into json:
        access_token = request.httprequest.headers.get('access_token')
        access_token_data = request.env['oauth.access_token'].sudo().search(
            [('token', '=', access_token)], order='id DESC', limit=1)

        if not access_token_data:
            error_descrip = "No access token was provided in request!"
            error = 'no_access_token'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        access_token_data.sudo().unlink()
        # Successful response:
        return successful_response(
            200,
            {}
        )

    @http.route([
        '/api/<model_name>',
        '/api/<model_name>/<id>'
    ], type='http', auth="none", methods=['POST', 'GET', 'PUT', 'DELETE'],
        csrf=False)
    @check_permissions
    def restapi_access_token(self, model_name=False, id=False, **post):
        Model = request.env['ir.model']
        Model_ids = Model.sudo().search([('model', '=', model_name),
                                  ('rest_api', '=', True)])
        if Model_ids:
            return getattr(self, '%s_data' % (
                request.httprequest.method).lower())(
                model_name=model_name, id=id, **post)
        return error_response_404__not_found_object_in_flectra()

    def get_data(self, model_name=False, id=False, **post):
        if id:
            return wrap__resource__read_one(
                modelname=model_name,
                id=id,
                success_code=200,
            )
        return wrap__resource__read_all(
            modelname=model_name,
            default_domain=[],
            success_code=200,
            post=post
        )

    def put_data(self, model_name=False, id=False, **post):
        return wrap__resource__update_one(
            modelname=model_name,
            id=id,
            success_code=200,
        )

    def post_data(self, model_name=False, id=False, **post):
        return wrap__resource__create_one(
            modelname=model_name,
            default_vals={},
            success_code=200,
        )

    def delete_data(self, model_name=False, id=False):
        return wrap__resource__delete_one(
            modelname=model_name,
            id=id,
            success_code=200
        )
