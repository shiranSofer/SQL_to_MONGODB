import sys

from subprocess import Popen, PIPE
from threading import Thread
from queue import Queue, Empty

mongoQuery = "db."
SQL_Logical_Operators = {"AND": "$and", "NOT": "$not", "OR": "$or"}
SQL_Comparison_Operators = {"=": "$eq", "!=": "$ne", "<>": "$ne", ">": "$gt", "<": "$lt", ">=": "$gte", "<=": "$lte", "!<": "$gt", "!>": "$lt", "NEQ": "$ne", "GEQ": "$gte", "LEQ": "$lte", "GTR": "$gt", "LSS": "$lt"}
SQL_String = ["char", "nchar", "varchar", "nvarchar"]
SQL_Int = ["int", "bigint", "decimal", "numeric", "number"]


def select_query():
    global mongoQuery, tableName

    def s_select():
        after_select = sqlQuery[sqlQuery.index("SELECT") + 1]
        if after_select == "*":
            return ""
        else:
            s_select_ret = ""
            after_select = sqlQuery[sqlQuery.index("SELECT") + 1:sqlQuery.index("FROM")]
            for w in after_select:
                if w[len(w)-1] == ",":
                    s_select_ret += w[:-1] + ": 1, "
                else:
                    s_select_ret += w + ": 1"
            return "{ " + s_select_ret + " }"

    def s_from():
        return sqlQuery[sqlQuery.index("FROM") + 1].lower()

    def s_where():
        s_where_ret = ""
        try:
            after_where = sqlQuery[sqlQuery.index("WHERE") + 1:]
            logical_op = None
            logical_op_flag = False
            i = 0
            while i != len(after_where):
                key = after_where[i]
                comp_op = after_where[i+1]
                val = after_where[i+2]
                i += 3
                if len(after_where) > 3 and i < len(after_where):
                    logical_op_flag = True
                    logical_op = after_where[i]
                    i += 1
                else:
                    logical_op = None
                if logical_op:
                    if logical_op in SQL_Logical_Operators:
                        s_where_ret += " { " + SQL_Logical_Operators[logical_op] + ": [ "
                    else:
                        raise QueryError
                if comp_op in SQL_Comparison_Operators:
                    s_where_ret += "{" + key + ": {" + SQL_Comparison_Operators[comp_op] + ": " + val + "} }"
                    if logical_op:
                        s_where_ret += " , "
                else:
                    raise QueryError
            if logical_op_flag:
                s_where_ret += " ] } "
        except ValueError:
            return "{ }"
        except:
            s_where_ret = -1
        return s_where_ret

    tableName = s_from()
    where_part = s_where()
    select_part = s_select()
    if where_part == -1:
        raise QueryError
    if select_part == "":
        return mongoQuery + tableName + ".find(" + where_part + select_part + ")"
    return mongoQuery + tableName + ".find(" + where_part + " , " + select_part + ")"


# .split("(", 1)[0]
def create_query():
    global mongoQuery, tableName
    tableName = sqlQuery[sqlQuery.index("TABLE") + 1].split("(", 1)[0]
    return mongoQuery + "createCollection(\"" + tableName + "\")"


def delete_query():

    def d_from():
        return sqlQuery[sqlQuery.index("FROM") + 1].lower()

    def d_where():
        d_where_ret = ""
        try:
            after_where = sqlQuery[sqlQuery.index("WHERE") + 1:]
            logical_op = None
            logical_op_flag = False
            i = 0
            while i != len(after_where):
                key = after_where[i]
                comp_op = after_where[i + 1]
                val = after_where[i + 2]
                i += 3
                if len(after_where) > 3 and i < len(after_where):
                    logical_op_flag = True
                    logical_op = after_where[i]
                    i += 1
                else:
                    logical_op = None
                if logical_op:
                    if logical_op in SQL_Logical_Operators:
                        d_where_ret += " { " + SQL_Logical_Operators[logical_op] + ": [ "
                    else:
                        raise QueryError
                if comp_op in SQL_Comparison_Operators:
                    d_where_ret += "{" + key + ": {" + SQL_Comparison_Operators[comp_op] + ": " + val + "} }"
                    if logical_op:
                        d_where_ret += " , "
                else:
                    raise QueryError
            if logical_op_flag:
                d_where_ret += " ] } "
        except ValueError:
            return "{ }"
        except:
            raise QueryError
        return d_where_ret

    tableName = d_from()
    return mongoQuery + tableName + ".deleteMany( " + d_where() + " )"


def insert_query():
    global sqlQuery, tableName

    def i_into():
        return sqlQuery[sqlQuery.index("INTO") + 1].lower().split("(", 1)[0]

    def i_values():
        global insert, sqlQuery, tableName
        i_values_ret = ""
        insert = "insertOne"
        i_values_ret_flag = False
        tableName = i_into()
        col = ' '.join(sqlQuery)
        col = col[col.index(tableName)+len(tableName)+1:]
        col = col[:col.index(")")].split(",")
        val = sqlQuery[sqlQuery.index("VALUES") + 1:]
        val = ''.join(val).replace("(", "")
        val = val.replace(")", "").split(",")
        if len(val) > len(col):
            insert = "insertMany"
            i_values_ret += "[ "
            i_values_ret_flag = True
        d = dict()
        for x in range(int(len(val)/len(col))):  # 0 - 1
            for i in range(len(col)):   # 0 - 2
                d[col[i]] = val[i+x*len(col)]
            i_values_ret += str(d)
            if i_values_ret_flag:
                i_values_ret += " , "
        if i_values_ret_flag:
            i_values_ret = i_values_ret[:-3]
            i_values_ret += " ]"
        return i_values_ret.replace("'", ""), insert

    tableName = i_into()
    i_val_ret = i_values()
    return mongoQuery + tableName + "." + i_val_ret[1] + "( " + i_val_ret[0] + " )"


functionSwitch = {"SELECT": select_query,  # SELECT .... FROM .... WHERE
                  "CREATE": create_query,  # CREATE TABLE .(NAME). ( comma seperated values )
                  "DELETE": delete_query,  # DELETE FROM .(NAME). WHERE
                  "INSERT": insert_query,  # INSERT INTO .(NAME). ( WHERE TO INSERT ? ) --> VALUES ( WHAT TO INSERT? )
                  "UPDATE": ()}  # UPDATE .(NAME). SET (WHO TO SET and WHAT) WHERE ....


class QueryError(Exception):
    pass


class NonBlockingStreamReader:
    def __init__(self, stream=None):
        # stream: the stream to read from.
        # Usually a process' stdout or stderr.
        self.is_running = False
        self._s = stream
        self._q = Queue()
        self._t = None

    @staticmethod
    def _populate_queue(stream, queue):
        # Collect lines from 'stream' and put them in 'queue'.
        while True:
            try:
                line = stream.readline()
            except ValueError:
                break
            if line:
                queue.put(line)
            else:
                pass

    def start(self):
        self.is_running = True
        self._t = Thread(target=self._populate_queue, args=(self._s, self._q))
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def get_is_running(self):
        return self.is_running

    def set_stream(self, s):
        self._s = s

    def get_stream(self):
        return self._s

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            pass


class UnexpectedEndOfStream(Exception):
    pass


def readNonBlocking():
    global nonBlocking
    str = ""
    while True:
        output = nonBlocking.readline(0.5)
        # 0.1 secs to let the shell output the result
        if not output:
            return str
        str += output


sqlQuery = []
# sqlQuery = sys.argv[1:]
sqlQuery = "INSERT INTO people(user_id, age, status) VALUES ('bcd001', 45, 'A')".split()
if sqlQuery[0] in functionSwitch:
    try:
        mongoQuery = functionSwitch[sqlQuery[0]]()
    except QueryError:
        mongoQuery = "Unable to convert query file"
else:
    mongoQuery = "Unable to convert query file"

# print(mongoQuery)

server = "mongodb://localhost:27017"
process = Popen(["mongo", server], stdin=PIPE, stdout=PIPE, shell=False, universal_newlines=True)
nonBlocking = NonBlockingStreamReader(stream=process.stdout)
nonBlocking.start()
readNonBlocking()
process.communicate(mongoQuery)[0]
answer = readNonBlocking()
print(answer, end='')
import sys

from subprocess import Popen, PIPE
from threading import Thread
from queue import Queue, Empty

mongoQuery = "db."
SQL_Logical_Operators = {"AND": "$and", "NOT": "$not", "OR": "$or"}
SQL_Comparison_Operators = {"=": "$eq", "!=": "$ne", "<>": "$ne", ">": "$gt", "<": "$lt", ">=": "$gte", "<=": "$lte", "!<": "$gt", "!>": "$lt", "NEQ": "$ne", "GEQ": "$gte", "LEQ": "$lte", "GTR": "$gt", "LSS": "$lt"}
SQL_String = ["char", "nchar", "varchar", "nvarchar"]
SQL_Int = ["int", "bigint", "decimal", "numeric", "number"]


def select_query():
    global mongoQuery, tableName

    def s_select():
        after_select = sqlQuery[sqlQuery.index("SELECT") + 1]
        if after_select == "*":
            return ""
        else:
            s_select_ret = ""
            after_select = sqlQuery[sqlQuery.index("SELECT") + 1:sqlQuery.index("FROM")]
            for w in after_select:
                if w[len(w)-1] == ",":
                    s_select_ret += w[:-1] + ": 1, "
                else:
                    s_select_ret += w + ": 1"
            return "{ " + s_select_ret + " }"

    def s_from():
        return sqlQuery[sqlQuery.index("FROM") + 1].lower()

    def s_where():
        s_where_ret = ""
        try:
            after_where = sqlQuery[sqlQuery.index("WHERE") + 1:]
            logical_op = None
            logical_op_flag = False
            i = 0
            while i != len(after_where):
                key = after_where[i]
                comp_op = after_where[i+1]
                val = after_where[i+2]
                i += 3
                if len(after_where) > 3 and i < len(after_where):
                    logical_op_flag = True
                    logical_op = after_where[i]
                    i += 1
                else:
                    logical_op = None
                if logical_op:
                    if logical_op in SQL_Logical_Operators:
                        s_where_ret += " { " + SQL_Logical_Operators[logical_op] + ": [ "
                    else:
                        raise QueryError
                if comp_op in SQL_Comparison_Operators:
                    s_where_ret += "{" + key + ": {" + SQL_Comparison_Operators[comp_op] + ": " + val + "} }"
                    if logical_op:
                        s_where_ret += " , "
                else:
                    raise QueryError
            if logical_op_flag:
                s_where_ret += " ] } "
        except ValueError:
            return "{ }"
        except:
            s_where_ret = -1
        return s_where_ret

    tableName = s_from()
    where_part = s_where()
    select_part = s_select()
    if where_part == -1:
        raise QueryError
    if select_part == "":
        return mongoQuery + tableName + ".find(" + where_part + select_part + ")"
    return mongoQuery + tableName + ".find(" + where_part + " , " + select_part + ")"


# .split("(", 1)[0]
def create_query():
    global mongoQuery, tableName
    tableName = sqlQuery[sqlQuery.index("TABLE") + 1].split("(", 1)[0]
    return mongoQuery + "createCollection(\"" + tableName + "\")"


def delete_query():

    def d_from():
        return sqlQuery[sqlQuery.index("FROM") + 1].lower()

    def d_where():
        d_where_ret = ""
        try:
            after_where = sqlQuery[sqlQuery.index("WHERE") + 1:]
            logical_op = None
            logical_op_flag = False
            i = 0
            while i != len(after_where):
                key = after_where[i]
                comp_op = after_where[i + 1]
                val = after_where[i + 2]
                i += 3
                if len(after_where) > 3 and i < len(after_where):
                    logical_op_flag = True
                    logical_op = after_where[i]
                    i += 1
                else:
                    logical_op = None
                if logical_op:
                    if logical_op in SQL_Logical_Operators:
                        d_where_ret += " { " + SQL_Logical_Operators[logical_op] + ": [ "
                    else:
                        raise QueryError
                if comp_op in SQL_Comparison_Operators:
                    d_where_ret += "{" + key + ": {" + SQL_Comparison_Operators[comp_op] + ": " + val + "} }"
                    if logical_op:
                        d_where_ret += " , "
                else:
                    raise QueryError
            if logical_op_flag:
                d_where_ret += " ] } "
        except ValueError:
            return "{ }"
        except:
            raise QueryError
        return d_where_ret

    tableName = d_from()
    return mongoQuery + tableName + ".deleteMany( " + d_where() + " )"


def insert_query():
    global sqlQuery, tableName

    def i_into():
        return sqlQuery[sqlQuery.index("INTO") + 1].lower().split("(", 1)[0]

    def i_values():
        global insert, sqlQuery, tableName
        i_values_ret = ""
        insert = "insertOne"
        i_values_ret_flag = False
        tableName = i_into()
        col = ' '.join(sqlQuery)
        col = col[col.index(tableName)+len(tableName)+1:]
        col = col[:col.index(")")].split(",")
        val = sqlQuery[sqlQuery.index("VALUES") + 1:]
        val = ''.join(val).replace("(", "")
        val = val.replace(")", "").split(",")
        if len(val) > len(col):
            insert = "insertMany"
            i_values_ret += "[ "
            i_values_ret_flag = True
        d = dict()
        for x in range(int(len(val)/len(col))):  # 0 - 1
            for i in range(len(col)):   # 0 - 2
                d[col[i]] = val[i+x*len(col)]
            i_values_ret += str(d)
            if i_values_ret_flag:
                i_values_ret += " , "
        if i_values_ret_flag:
            i_values_ret = i_values_ret[:-3]
            i_values_ret += " ]"
        return i_values_ret.replace("'", ""), insert

    tableName = i_into()
    i_val_ret = i_values()
    return mongoQuery + tableName + "." + i_val_ret[1] + "( " + i_val_ret[0] + " )"


functionSwitch = {"SELECT": select_query,  # SELECT .... FROM .... WHERE
                  "CREATE": create_query,  # CREATE TABLE .(NAME). ( comma seperated values )
                  "DELETE": delete_query,  # DELETE FROM .(NAME). WHERE
                  "INSERT": insert_query,  # INSERT INTO .(NAME). ( WHERE TO INSERT ? ) --> VALUES ( WHAT TO INSERT? )
                  "UPDATE": ()}  # UPDATE .(NAME). SET (WHO TO SET and WHAT) WHERE ....


class QueryError(Exception):
    pass


class NonBlockingStreamReader:
    def __init__(self, stream=None):
        # stream: the stream to read from.
        # Usually a process' stdout or stderr.
        self.is_running = False
        self._s = stream
        self._q = Queue()
        self._t = None

    @staticmethod
    def _populate_queue(stream, queue):
        # Collect lines from 'stream' and put them in 'queue'.
        while True:
            try:
                line = stream.readline()
            except ValueError:
                break
            if line:
                queue.put(line)
            else:
                pass

    def start(self):
        self.is_running = True
        self._t = Thread(target=self._populate_queue, args=(self._s, self._q))
        self._t.daemon = True
        self._t.start()  # start collecting lines from the stream

    def get_is_running(self):
        return self.is_running

    def set_stream(self, s):
        self._s = s

    def get_stream(self):
        return self._s

    def readline(self, timeout=None):
        try:
            return self._q.get(block=timeout is not None, timeout=timeout)
        except Empty:
            pass


class UnexpectedEndOfStream(Exception):
    pass


def readNonBlocking():
    global nonBlocking
    str = ""
    while True:
        output = nonBlocking.readline(5)
        # 0.1 secs to let the shell output the result
        if not output:
            return str
        str += output


sqlQuery = []
sqlQuery = sys.argv[1:]
# sqlQuery = "SELECT * FROM sofer".split()
if sqlQuery[0] in functionSwitch:
    try:
        mongoQuery = functionSwitch[sqlQuery[0]]()
    except QueryError:
        mongoQuery = "Unable to convert query file"
else:
    mongoQuery = "Unable to convert query file"

# print(mongoQuery)

server = "mongodb://localhost:27017"
process = Popen(["mongo", server], stdin=PIPE, stdout=PIPE, shell=False, universal_newlines=True)
# nonBlocking = NonBlockingStreamReader(stream=process.stdout)
# nonBlocking.start()
# readNonBlocking()
answer = process.communicate(mongoQuery)[0]
index = answer.find('{')
print(index)
final = answer[index + 1:-4]
index = final.find('{')
# answer = readNonBlocking()
print(mongoQuery + "`" + final[index:].replace("\n","@"), end='')
