import hashlib, struct
from datetime import datetime

class dga():
    def __init__(self):
        self.tlds = [ # list of top level domains
            '.ru',
            '.com',
            '.xyz',
            '.biz',
            '.net',
            '.nl'
        ]

    def get_seed(self, seq_nr, date):
        '''
        Creates a seed based off the current date and a sequence number
        '''

        seq_nr = struct.pack('<I', seq_nr) 
        year = struct.pack('<H', date.year)
        month = struct.pack('<H', date.month)
        day = struct.pack('<H', date.day)

        m = hashlib.sha256(str(seq_nr).encode())
        m.update(seq_nr)
        m.update(year); m.update(seq_nr)
        m.update(month); m.update(seq_nr)
        m.update(day); m.update(seq_nr)

        return m.hexdigest()

    def create_domain(self, seq_nr, date):
        '''
        Creates a random domain from a seed number, and a date
        '''

        def generate_domain_part(seed, nr):
            part = [] 

            for _ in range(nr*2):
                edx = seed%34
                seed //= 34

                part +=  chr(ord('a') + (edx-10)) if edx > 9 else chr(edx + ord('0'))
                if seed == 0: break

            part = part[::-1] if nr%2 == 0 else part
            return ''.join(part)    

        def hex_to_int(seed):
            seed = ''.join(reversed([seed[x:x+2] for x in range(0, 8, 2)]))
            return int(seed,16)

        seed_value = self.get_seed(seq_nr, date)
        domain = ""

        for i in range(0,16,4): domain += generate_domain_part(hex_to_int(seed_value[i*4:i*4+20]), 20)

        tlds = ['.com','.org','.biz','.net','neocities.org','dyndns.org','duckdns.org','mooo.com','chickenkiller.com']
        try: tld = tlds[seq_nr%len(tlds)]
        except: tld = '.net'

        return domain+tld

print(dga().create_domain(1, datetime.now()))