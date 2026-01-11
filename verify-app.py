import csv
import io
import re
import time
import uuid
import dns.resolver
import smtplib
import threading
from concurrent.futures import ThreadPoolExecutor
from flask import Flask, request, jsonify, send_file, Response
from flask_cors import CORS
from tempfile import NamedTemporaryFile

app = Flask(__name__)
CORS(app)

print("\U0001F525 HIZLANDIRILMIŞ DOĞRULAYICI ÇALIŞIYOR - Thread Pool Aktif \U0001F525")

EMAIL_REGEX = re.compile(r"[^@]+@[^@]+\.[^@]+")
DISPOSABLE_DOMAINS = {"mailinator.com", "10minutemail.com", "guerrillamail.com"}
ROLE_BASED_PREFIXES = {"info", "support", "admin", "sales", "contact"}


data = {}


def check_email(email):

    if not EMAIL_REGEX.match(email):
        return "invalid", "bad_syntax"

    domain = email.split('@')[1]
    local = email.split('@')[0]

    if domain.lower() in DISPOSABLE_DOMAINS:
        return "invalid", "disposable_domain"
    if local.lower() in ROLE_BASED_PREFIXES:
        return "invalid", "role_based"

    try:

        resolver = dns.resolver.Resolver()
        resolver.lifetime = 5
        records = resolver.resolve(domain, 'MX')
        mx_record = str(records[0].exchange)
    except Exception:
        return "invalid", "no_mx"

    def smtp_check(target_email):
        try:

            server = smtplib.SMTP(timeout=7)
            server.connect(mx_record)
            server.helo("example.com")
            server.mail("verifier@example.com")
            code, _ = server.rcpt(target_email)
            server.quit()
            return code
        except Exception:
            return None


    code = smtp_check(email)


    if code in [421, 450, 451, 452, 503]:
        time.sleep(2)
        code = smtp_check(email)

    if code == 250:
        return "valid", "smtp_ok"
    elif code is None:
        return "risky", "smtp_timeout"
    elif code in [421, 450, 451, 452, 503]:
        return "risky", f"smtp_soft_fail_{code}"
    elif code == 550:
        return "invalid", "smtp_reject"
    else:
        return "invalid", f"smtp_{code}"


def process_row(job_id, row, email_field, index, total):

    if data[job_id]['cancel']:
        return None

    email = (row.get(email_field) or '').strip()
    if not email:
        status, reason = 'invalid', 'empty_email'
    else:
        status, reason = check_email(email)

    row['status'], row['reason'] = status, reason


    data[job_id]['row'] += 1
    current_row = data[job_id]['row']
    percent = int((current_row / total) * 100)
    data[job_id]['progress'] = percent
    data[job_id]['log'] = f"\u2705 {email} -> {status}"

    return row


@app.route('/verify', methods=['POST'])
def verify():
    job_id = str(uuid.uuid4())
    file = request.files['file']
    content = file.read().decode('utf-8')
    reader = list(csv.DictReader(io.StringIO(content)))
    total = len(reader)

    if total == 0:
        return jsonify({"error": "Dosya boş"}), 400

    email_field = next((f for f in reader[0].keys() if f.lower().strip() == 'email'), None)

    if not email_field:
        return jsonify({"error": "Email sütunu bulunamadı"}), 400

    data[job_id] = {
        "progress": 0,
        "row": 0,
        "total": total,
        "log": "Başlatılıyor...",
        "cancel": False,
        "results": [],
        "filename": file.filename,
        "fieldnames": list(reader[0].keys()) + ['status', 'reason']
    }

    def run_parallel():

        with ThreadPoolExecutor(max_workers=15) as executor:
            futures = [executor.submit(process_row, job_id, row, email_field, i, total)
                       for i, row in enumerate(reader)]

            final_results = []
            for f in futures:
                res = f.result()
                if res:
                    final_results.append(res)

            data[job_id]['results'] = final_results
            data[job_id]['log'] = "Tamamlandı!"

    threading.Thread(target=run_parallel).start()
    return jsonify({"job_id": job_id})


@app.route('/progress')
def progress():
    job_id = request.args.get("job_id")
    d = data.get(job_id, {})
    return jsonify({
        "percent": d.get("progress", 0),
        "row": d.get("row", 0),
        "total": d.get("total", 0)
    })


@app.route('/log')
def log():
    job_id = request.args.get("job_id")
    return Response(data.get(job_id, {}).get("log", ""), mimetype='text/plain')


@app.route('/download')
def download():
    job_id = request.args.get("job_id")
    filter_type = request.args.get("type", "all")
    job = data.get(job_id)

    if not job or not job['results']:
        return "Dosya hazır değil veya iş bulunamadı", 404

    results = job['results']
    if filter_type == "valid":
        filtered = [r for r in results if r['status'] == 'valid']
    elif filter_type == "risky":
        filtered = [r for r in results if r['status'] == 'risky']
    else:
        filtered = results

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=job['fieldnames'])
    writer.writeheader()
    writer.writerows(filtered)

    return Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment; filename={filter_type}_{job['filename']}"}
    )


if __name__ == '__main__':

    app.run(debug=True, port=5050)