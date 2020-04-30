from __future__ import division
from flask import Flask,request,render_template,redirect
from flask_cors import CORS
import datetime,pygal
from random import random

def now(): return datetime.datetime.today()

global last_request, SIM_RESULTS, SERVER_PORT, SERVER_HOST

last_request = now()
SIM_RESULTS = {
    "Normal":[],
    "Sensor":[],
    "last_settings":{"xdata":[]}
}
SERVER_PORT = 5000
SERVER_HOST = "localhost"

app = Flask(__name__)
CORS(app)

@app.route("/assets/<path:asset>")
def serve_asset(asset):
    return app.send_static_file(asset)

def car_data(ns,ss):
    data = []
    for j in xrange(4):
        n_cars = ns[j]
        s = ss[j]
        for i in xrange(n_cars):
            if j == 0:
                data.append("{x:canvas.width*(0.0074+2*%s*0.0159),y:0.62157*canvas.height,speed:{x:%s, y:0},h:0.01828*canvas.width,w:0.0159*canvas.height,stroke:'black',fill:'yellow',lane:1,braking:0.38788*canvas.width,collision:false}" % (i,s))
            if j == 1:
                data.append("{x:canvas.width*(0.9968-2*%s*0.0159),y:0.36928*canvas.height,speed:{x:-1*%s, y:0},h:0.01828*canvas.width,w:0.0159*canvas.height,stroke:'black',fill:'yellow',lane:2,braking:0.608926*canvas.width,collision:false}" % (i,s))
            if j == 2:
                data.append("{y:canvas.width*(0.007312+2*%s*0.0159),x:0.434*canvas.width,speed:{x:0, y:%s},w:0.01828*canvas.width,h:0.0159*canvas.height,stroke:'black',fill:'yellow',lane:3,braking:0.28233*canvas.height,collision:false}" % (i,s))
            if j == 3:
                data.append("{y:canvas.width*(0.9968-2*%s*0.0159),x:0.551*canvas.width,speed:{x:0, y:-1*%s},w:0.01828*canvas.width,h:0.0159*canvas.height,stroke:'black',fill:'yellow',lane:4,braking:0.704918*canvas.height,collision:false}" % (i,s))
    return ",".join(data)

@app.route("/traffic/analytics/refresh")
def refresh_data():
    global SIM_RESULTS
    SIM_RESULTS = {
        "Normal":[],
        "Sensor":[],
        "last_settings":{"xdata":[]}
    }
    return "200 OK"

@app.route("/traffic/analytics/store")
def store_game_results():
    global SIM_RESULTS
    params = dict(request.args)
    params = {key.lower():params[key][-1] for key in params}
    pass_rate = params["pass_rate"]
    wait_time = params["wait_time"]
    deadlock = params["deadlock"]
    mode = params["mode"]
    SIM_RESULTS[mode].append((pass_rate,wait_time,deadlock,SIM_RESULTS["last_settings"]["congestion"],SIM_RESULTS["last_settings"]["speed"]))
    SIM_RESULTS = SIM_RESULTS
    return "200 OK"

@app.route("/traffic/analytics/view-data")
def view_data():
    return str(SIM_RESULTS)

def delta(s,n):
    try:
        return 100*(s/n - 1)
    except:
        return 0

def chart(title,deltas):
    c = pygal.HorizontalBar()
    c.title = title
    j = 0
    for delta in deltas:
        j+=1
        c.add('delta %s' % delta, delta)
    return c.render_data_uri()

@app.route("/traffic/analytics/compare/<path:cycles>")
def compare_data(cycles):
    cycles = int(float(cycles))
    report = {
        "pass_rate":{
            "w_deadlock":[],
            "n_deadlock":[],
            "failed":0,
            "passed":0,
            "delta":[]
        },
        "wait_time":{
            "w_deadlock":[],
            "n_deadlock":[],
            "failed":0,
            "passed":0,
            "delta":[]
        }
    }
    for i in xrange(int(cycles/2)):
        n = SIM_RESULTS["Normal"][i]
        s = SIM_RESULTS["Sensor"][i]
        if float(s[0]) >= float(n[0]):
            if eval(s[2].title()):
                report["pass_rate"]["w_deadlock"].append(s[3:])
            else:
                report["pass_rate"]["n_deadlock"].append(s[3:])
            report["pass_rate"]["passed"]+=1
        else:
            report["pass_rate"]["failed"]+=1
        report["pass_rate"]["delta"].append(delta(float(s[0]),float(n[0])))
        if float(s[1]) <= float(n[1]):
            if eval(s[2].title()):
                report["wait_time"]["w_deadlock"].append(s[3:])
            else:
                report["wait_time"]["n_deadlock"].append(s[3:])
            report["wait_time"]["passed"]+=1
        else:
            report["wait_time"]["failed"]+=1
        report["wait_time"]["delta"].append(delta(float(s[1]),float(n[1])))
    pass_rate_delta_chart = chart("Pass Rate Delta Chart",report["pass_rate"]["delta"])
    wait_time_delta_chart = chart("Wait Time Delta Chart",report["wait_time"]["delta"])
    average_pass_rate_delta = sum(report["pass_rate"]["delta"])/len(report["pass_rate"]["delta"])
    average_wait_time_delta = sum(report["wait_time"]["delta"])/len(report["wait_time"]["delta"])
    pass_rate_success_scenarios_deadlock_table = """
        <table>
        <tr><th><b>Congestion Profile</b></th><th><b>Speed Profile</b></th></tr>
          __ROWS__
        </table>
    """
    row_html = ""
    for entry in report["pass_rate"]["w_deadlock"]:
        row_html+="<td>%s</td><td>%s</td>" % ("-".join(map(str,entry[0])),"-".join(map(str,entry[1])))
    pass_rate_success_scenarios_deadlock_table = pass_rate_success_scenarios_deadlock_table.replace("__ROWS__",row_html)
    pass_rate_success_scenarios_no_deadlock_table = """
        <table>
        <tr><th><b>Congestion Profile</b></th><th><b>Speed Profile</b></th></tr>
          __ROWS__
        </table>
    """
    row_html = ""
    for entry in report["pass_rate"]["n_deadlock"]:
        row_html+="<td>%s</td><td>%s</td>" % ("-".join(map(str,entry[0])),"-".join(map(str,entry[1])))
    pass_rate_success_scenarios_no_deadlock_table = pass_rate_success_scenarios_no_deadlock_table.replace("__ROWS__",row_html)
    wait_time_success_scenarios_deadlock_table = """
        <table>
        <tr><th><b>Congestion Profile</b></th><th><b>Speed Profile</b></th></tr>
          __ROWS__
        </table>
    """
    row_html = ""
    for entry in report["wait_time"]["w_deadlock"]:
        row_html+="<td>%s</td><td>%s</td>" % ("-".join(map(str,entry[0])),"-".join(map(str,entry[1])))
    wait_time_success_scenarios_deadlock_table = wait_time_success_scenarios_deadlock_table.replace("__ROWS__",row_html)
    wait_time_success_scenarios_no_deadlock_table = """
        <table>
        <tr><th><b>Congestion Profile</b></th><th><b>Speed Profile</b></th></tr>
          __ROWS__
        </table>
    """
    row_html = ""
    for entry in report["wait_time"]["n_deadlock"]:
        row_html+="<td>%s</td><td>%s</td>" % ("-".join(map(str,entry[0])),"-".join(map(str,entry[1])))
    wait_time_success_scenarios_no_deadlock_table = wait_time_success_scenarios_no_deadlock_table.replace("__ROWS__",row_html)
    refresh_data()
    return render_template("results.html",pass_rate_delta_chart=pass_rate_delta_chart,pass_rate_failed=report["pass_rate"]["failed"],pass_rate_passed=report["pass_rate"]["passed"],pass_rate_success_scenarios_deadlock_table=pass_rate_success_scenarios_deadlock_table,pass_rate_success_scenarios_no_deadlock_table=pass_rate_success_scenarios_no_deadlock_table,wait_time_delta_chart=wait_time_delta_chart,wait_time_failed=report["wait_time"]["failed"],wait_time_passed=report["wait_time"]["passed"],wait_time_success_scenarios_deadlock_table=wait_time_success_scenarios_deadlock_table,wait_time_success_scenarios_no_deadlock_table=wait_time_success_scenarios_no_deadlock_table,average_pass_rate_delta=average_pass_rate_delta,average_wait_time_delta=average_wait_time_delta)

@app.route("/traffic/test/controller/<path:cycles>")
def controlled_test(cycles):
    try:
        global SIM_RESULTS
        max_cycles = 100
        def r_tl():return int(50 + random()*150)
        def r_cs():return 0.1 + random()*0.9
        try:
            cycles = int(float(cycles))
        except:
            cycles = -1
        cycles+=1
        if cycles <= 2*max_cycles:
            if cycles == 0:
                refresh_data()
            if cycles <= max_cycles:
                mode = "Normal"
                TL = r_tl()
                C = ",".join(map(str,[r_cs() for i in xrange(4)]))
                S = ",".join(map(str,[r_cs() for i in xrange(4)]))
                SIM_RESULTS["last_settings"]["xdata"].append((TL,C,S))
            else:
                mode = "Sensor"
                TL,C,S = SIM_RESULTS["last_settings"]["xdata"][cycles - (max_cycles+1)]
            refresh_url = "https://traffic-simulator.herokuapp.com/traffic/test/controller/%s" % (cycles)
            url = "https://traffic-simulator.herokuapp.com/traffic/simulate?refresh_url=%s&tl_interval=%s&mode=%s&congestion=%s&speed=%s" % (refresh_url,TL,mode,C,S)
            return redirect(url,302)
        else:
            return compare_data(max_cycles)
    except:
        return redirect("https://traffic-simulator.herokuapp.com/traffic/test/controller/0", 302)

@app.route("/traffic/simulate")
def simulator():
    global last_request, SIM_RESULTS, cs, ss
    SIM_LASTED = (now() - last_request).seconds*600; last_request = now()
    params = dict(request.args)
    params = {key.lower():params[key][-1] for key in params}
    if "refresh_url" in params:
        REFRESH_URL = params["refresh_url"]
    else:
        REFRESH_URL = request.url
    if "sim_rounds" in params:
        try:
            SIM_ROUNDS = int(float(params["sim_rounds"]))
        except:
            SIM_ROUNDS = 700
    else:
        SIM_ROUNDS = 700
    if "tl_interval" in params:
        try:
            TL_INTERVAL = int(float(params["tl_interval"]))
        except:
            TL_INTERVAL = 100
    else:
        TL_INTERVAL = 100
    if "mode" in params:
        TRAFFIC_MODE = params["mode"]
    else:
        TRAFFIC_MODE = "Normal"
    if "congestion" in params:
        try:
            cs = map(float,[x for x in params["congestion"].split(",") if x]); n_cars = []
            j = -1
            for c in cs:
                j+=1
                if c > 1 or c < 0:
                    c = 0.5
                if j < 2:
                    n_cars.append(int(c*12))
                else:
                    n_cars.append(int(c*6))
            if len(n_cars) > 4:
                n_cars = n_cars[:4]
            if len(n_cars) < 4:
                diff = 4 - len(n_cars)
                for i in xrange(diff):
                    n_cars.append(4)
        except:
            cs = [0.5,0.5,0.5,0.5]
            n_cars = [6,6,6,6]
    else:
        cs = [0.5,0.5,0.5,0.5]
        n_cars = [6,6,6,6]
    if "speed" in params:
        try:
            ss = map(float,[x for x in params["speed"].split(",") if x]); s_cars = []
            for s in ss:
                if s > 1 or s < 0:
                    s = 0.5
                s_cars.append(int(s*15))
            if len(s_cars) > 4:
                s_cars = s_cars[:4]
            if len(s_cars) < 4:
                diff = 4 - len(s_cars)
                for i in xrange(diff):
                    s_cars.append(7)
        except:
            ss = [0.5,0.5,0.5,0.5]
            s_cars = [7,7,7,7]
    else:
        ss = [0.5,0.5,0.5,0.5]
        s_cars = [7,7,7,7]

    SIM_RESULTS["last_settings"]["sim_rounds"] = SIM_ROUNDS
    SIM_RESULTS["last_settings"]["tl_interval"] = TL_INTERVAL
    SIM_RESULTS["last_settings"]["mode"] = TRAFFIC_MODE
    SIM_RESULTS["last_settings"]["congestion"] = cs
    SIM_RESULTS["last_settings"]["speed"] = ss

    DYNAMIC_CODE = """

        var TRAFFIC_MODE = '__MODE__';
        var objects = [

          __CAR_DATA__,
          {x:0.4*canvas.width, y:0.68*canvas.height, speed:{x:0, y:0}, w:0.009574*canvas.width, h:0.02*canvas.height, stroke:"white", fill:"green",lane:1},
          {x:0.59*canvas.width, y:0.30*canvas.height, speed:{x:0, y:0}, w:0.009574*canvas.width, h:0.02*canvas.height, stroke:"white", fill:"green",lane:2},
          {x:0.4*canvas.width, y:0.30*canvas.height, speed:{x:0, y:0}, w:0.009574*canvas.width, h:0.02*canvas.height, stroke:"white", fill:"red",lane:3},
          {x:0.59*canvas.width, y:0.68*canvas.height, speed:{x:0, y:0}, w:0.009574*canvas.width, h:0.02*canvas.height, stroke:"white", fill:"red",lane:4}
        ]
    """
    DYNAMIC_CODE = DYNAMIC_CODE.replace("__CAR_DATA__",car_data(n_cars,s_cars))
    DYNAMIC_CODE = DYNAMIC_CODE.replace("__MODE__",TRAFFIC_MODE)
    return render_template("render.html",DYNAMIC_CODE=DYNAMIC_CODE,REFRESH_URL=REFRESH_URL,TRAFFIC_MODE=TRAFFIC_MODE,SIM_LASTED=SIM_LASTED,SIM_ROUNDS=SIM_ROUNDS,TL_INTERVAL=TL_INTERVAL)

if __name__ == "__main__":
  app.run(host=SERVER_HOST,port=SERVER_PORT,threaded=True)
