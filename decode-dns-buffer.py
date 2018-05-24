#!/usr/bin/env python

import sys
import pprint
import struct
import base64

if len(sys.argv) < 2:
    print('Usage: parse.py MEASUREMENT_ID')
    sys.exit(1)

def decode_header(message):
    header_format = struct.Struct("!6H")
    id, fields, qdcount, ancount, nscount, arcount = header_format.unpack_from(message)

    rcode = fields & 0b1111
    z = (fields >> 4) & 0b111
    ra = (fields >> 7) & 1
    rd = (fields >> 8) & 1
    tc = (fields >> 9) & 1
    aa = (fields >> 10) & 1
    opcode = (fields >> 11) & 0b1111
    qr = (fields >> 15) & 1

    header = {
        "id": id,
        "qr": qr,
        "opcode": opcode,
        "aa": aa,
        "tc": tc,
        "rd": rd,
        "ra": ra,
        "z": z,
        "rcode": rcode,
        "qdcount": qdcount,
        "ancount": ancount,
        "nscount": nscount,
        "arcount": arcount
    }

    offset = header_format.size

    return header, offset

def decode_labels(message, offset):
    labels = []

    while True:
        length, = struct.unpack_from("!B", message, offset)

        if (length >> 6) == 0b11:
            pointer, = struct.unpack_from("!H", message, offset)
            offset += 2

            # get rid of the 2 highest order bits since they are no part of the offset
            # 0x3FFF = 00111111 11111111
            pointer = pointer & 0x3FFF
            label = decode_labels(message, pointer)[0]

            return labels + label, offset

        offset += 1

        if length == 0:
            return labels, offset

        labels.append(*struct.unpack_from("!%ds" % length, message, offset))
        offset += length

def decode_rr(message, offset):
    rr_format = struct.Struct("!2HIH")

    name, offset = decode_labels(message, offset)
    atype, aclass, ttl, rdlength = rr_format.unpack_from(message, offset)
    offset += rr_format.size

    rr = {"name": name,
                "type": atype,
                "class": aclass,
                "ttl": ttl,
                "rdlength": rdlength}
    
    if atype == 1:
        a_field = struct.Struct('!4B')
        ip1, ip2, ip3, ip4 = a_field.unpack_from(message, offset)
        offset += a_field.size
        rr['address'] = '%i.%i.%i.%i' % (ip1, ip2, ip3, ip4 )
    elif atype == 2:
        rr['nsdname'], offset = decode_labels(message, offset)
    elif atype == 6:
        soa_fields = struct.Struct("!5I")
        mname, offset = decode_labels(message, offset)
        rname, offset = decode_labels(message, offset)
        serial, refresh, retry, expire, minimum = soa_fields.unpack_from(message, offset)
        offset += soa_fields.size

        rr['mname'] = mname
        rr['rname'] = rname
        rr['serial'] = serial
        rr['refresh'] = refresh
        rr['retry'] = retry
        rr['expire'] = expire
        rr['minimum'] = minimum

    return rr, offset

def decode_question(message, offset, qdcount):
    questions = []
    question_format = struct.Struct("!2H")

    for _ in range(qdcount):
        qname, offset = decode_labels(message, offset)

        qtype, qclass = question_format.unpack_from(message, offset)
        offset += question_format.size

        question = {
            "qname": qname,
            "qtype": qtype,
            "qclass": qclass
        }

        questions.append(question)

    return questions, offset

def decode_answer_section(message, offset, ancount):
    answers = []

    for _ in range(ancount):
        answer, offset = decode_rr(message, offset)
        answers.append(answer)

    return answers, offset

def decode_dns_message(message):
    header, offset = decode_header(message)
    questions, offset = decode_question(message, offset, header['qdcount'])
    answers, offset = decode_answer_section(message, offset, header['ancount'])
    authority, offset = decode_answer_section(message, offset, header['nscount'])
    additional, offset = decode_answer_section(message, offset, header['arcount'])

    result = {
        "header": header,
        "question": questions,
        "answer": answers,
        "authority": authority,
        "additional": additional
    }

    return result

def str_question(q):
    if q['qclass'] == 1:
        qclass = 'IN'

    if q['qtype'] == 1:
        qtype = 'A'
    elif q['qtype'] == 2:
        qtype = 'NS'
    elif q['qtype'] == 6:
        qtype = 'SOA'

    return '.'.join(q['qname']) + '. ' + qclass + ' ' + qtype

def str_rr(rr):
    if rr['class'] == 1:
        rrclass = 'IN'

    if rr['type'] == 1:
        return '%s. %i %s A %s' % (
            '.'.join(rr['name']),
            rr['ttl'],
            rrclass,
            rr['address'])
    if rr['type'] == 2:
        return '%s. %i %s NS %s' % (
            '.'.join(rr['name']),
            rr['ttl'],
            rrclass,
            '.'.join(rr['nsdname']))
    elif rr['type'] == 6:
        return '%s. %i %s SOA %s %s %s %s %s %s %s' % (
            '.'.join(rr['name']),
            rr['ttl'],
            rrclass,
            '.'.join(rr['mname']),
            '.'.join(rr['rname']),
            rr['serial'],
            rr['refresh'],
            rr['retry'],
            rr['expire'],
            rr['minimum'])
    else:
        return '*Not implemented*'

def print_dns_message(message):
    result = decode_dns_message(message)
    print_result = []

    h = result['header']
    print_result.append([
        'Header',
        '------',
        'ID=%s' % result['header']['id'],
        'QR=%s OPCODE=%s AA=%s TC=%s RD=%s RA=%s Z=%s RCODE=%s' % (h['qr'], h['opcode'], h['aa'], h['tc'], h['rd'], h['ra'], h['z'], h['opcode']),
        'QDCOUNT=%s ANCOUNT=%s NSCOUNT=%s ARCOUNT=%s' % (h['qdcount'], h['ancount'], h['nscount'], h['arcount']) 
    ])

    print_result.append(['Question', '--------'])
    for q in result['question']:
        print_result[1].append(str_question(q))

    print_result.append(['Answer', '------'])
    for a in result['answer']:
        print_result[2].append(str_rr(a))

    print_result.append(['Authority', '---------'])
    for a in result['authority']:
        print_result[3].append(str_rr(a))

    print_result.append(['Additional', '----------'])
    for a in result['additional']:
        print_result[4].append(str_rr(a))

    max_len = 0
    for row in print_result:
        for line in row:
            if max_len < len(line):
                max_len = len(line)
    if max_len > 76:
        max_len = 76
    
    output = ''
    for row in print_result:
        output += '+' + '-' * (max_len + 2) + '+\n'
        for line in row:
            if len(line) <= max_len:
                output += '| ' + line + ' ' * (max_len - len(line) + 1) + '|\n'
            else:
                for i in range(len(line) // max_len + 1):
                    output += '/ ' + line[i*max_len:(i+1)*max_len] + ' ' * (max_len - len(line[i*max_len:(i+1)*max_len]) + 1) + '/\n'
    output += '+' + '-' * (max_len + 2) + '+\n'

    print(output)

data = base64.b64decode(sys.argv[1])
#pprint.pprint(decode_dns_message(data))
print_dns_message(data)

#file = open('testquery.bin', 'rb')
#print_dns_message(file.read())
