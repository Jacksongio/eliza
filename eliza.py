import re
import random
import json
import string

#pronoun dict
PRONOUN_MAP = {
    'I': 'YOU',
    'ME': 'YOU',
    'MY': 'YOUR',
    'AM': 'ARE',
    'MYSELF': 'YOURSELF',
    'MINE': 'YOURS',
    'YOU': 'I',
    'YOUR': 'MY',
    'YOURS': 'MINE',
    'ARE': 'AM',
    'YOURSELF': 'MYSELF'
}

class Eliza:
    def __init__(self, rules):
        self.rules = rules
        self.memory = []
        self.none_ptr = 0 
        self.last_reass = {} 

    def swap_pronouns(self, text):
        if not text:
            return ''
        words = text.split()
        swapped = []
        for word in words:
            if word in PRONOUN_MAP:
                swapped.append(PRONOUN_MAP[word])
            else:
                swapped.append(word)
        return ' '.join(swapped)

    def pattern_to_regex(self, pattern):
        regex_parts = []
        for p in pattern:
            if p == 0:
                regex_parts.append('(.*?)')
            else:
                regex_parts.append(re.escape(str(p)))
        regex_str = r'^\s*' + r'\s+'.join(regex_parts) + r'\s*$'
        return re.compile(regex_str)

    def extract_parts(self, pattern, match):
        groups = match.groups()
        group_idx = 0
        parts = []
        for p in pattern:
            if p == 0:
                captured = groups[group_idx].strip()
                parts.append(captured.split() if captured else [])
                group_idx += 1
            else:
                parts.append([p])
        return parts

    def build_response(self, reassembly, parts):
        response_parts = []
        for item in reassembly:
            if isinstance(item, int):
                if item > 0 and item <= len(parts):
                    part_text = ' '.join(parts[item - 1])  # 1-indexed
                    transformed = self.swap_pronouns(part_text)
                    response_parts.append(transformed)
            else:
                response_parts.append(item)
        response = ' '.join(response_parts)
        #clean punctuation
        response = re.sub(r'\s+([?.!,])', r'\1', response)
        return response



    def generate_response(self, user_input):
        #normalize the input
        user_input = user_input.upper()
        translator = str.maketrans('', '', string.punctuation)
        cleaned = user_input.translate(translator)
        input_words = cleaned.split()

        if not input_words:
            return self.cycle_none()

        #candidate keywords
        candidates = []
        for keyword, data in self.rules.items():
            if keyword == 'NONE':
                continue  # Skip NONE for normal search
            kw_upper = keyword.upper()
            precedence = data.get('precedence', 0)
            try:
                index = input_words.index(kw_upper)
                candidates.append((keyword, precedence, index))
            except ValueError:
                pass

        if not candidates:
            return self.use_memory_or_none()

        #sorting
        candidates.sort(key=lambda x: (-x[1], x[2]))

        #selecting the keywords
        selected_keyword = candidates[0][0]
        selected_data = self.rules[selected_keyword]

        input_text = ' '.join(input_words)

        #now utilizing the rules i made
        for rule in selected_data['rules']:
            decomp = rule['decomp']
            regex = self.pattern_to_regex(decomp)
            match = regex.match(input_text)
            if match:
                parts = self.extract_parts(decomp, match)
                reassemblies = rule['reass']
                if len(reassemblies) > 1 and selected_keyword in self.last_reass:
                    avail = [r for i, r in enumerate(reassemblies) if i != self.last_reass[selected_keyword]]
                    reassembly = random.choice(avail)
                else:
                    reassembly = random.choice(reassemblies)
                self.last_reass[selected_keyword] = reassemblies.index(reassembly)
                response = self.build_response(reassembly, parts)

                # Handle memory save if present
                if 'memory' in rule:
                    mem = rule['memory']
                    mem_decomp = mem['decomp']
                    mem_regex = self.pattern_to_regex(mem_decomp)
                    mem_match = mem_regex.match(input_text)
                    if mem_match:
                        mem_parts = self.extract_parts(mem_decomp, mem_match)
                        mem_save = mem['save']
                        mem_reass = random.choice(mem_save)
                        mem_response = self.build_response(mem_reass, mem_parts)
                        self.memory.append(mem_response)

                return response

        return self.use_memory_or_none()

    def use_memory_or_none(self):
        if self.memory:
            return self.memory.pop()
        else:
            return self.cycle_none()

    def cycle_none(self):
        none_data = self.rules.get('NONE', {})
        if none_data:
            none_reass = none_data['rules'][0]['reass']
            response = ' '.join(none_reass[self.none_ptr])
            self.none_ptr = (self.none_ptr + 1) % len(none_reass)
            return response
        else:
            return "PLEASE GO ON."



def main(script_file='eliza_script.json'):
    try:
        with open(script_file, 'r') as f:
            rules = json.load(f)
    except FileNotFoundError:
        print(f"Error: Script file '{script_file}' not found.")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON in script file.")
        return

    eliza = Eliza(rules)

    # Welcome
    print("HELLO, I'M ELIZA. ASK ME A QUESTION OR TALK ABOUT ANYTHING? (TYPE 'QUIT' TO EXIT)")

    while True:
        user_input = input("> ").strip()
        if user_input.lower() in ['quit', 'exit', 'goodbye']:
            print("GOODBYE!")
            break
        response = eliza.generate_response(user_input)
        print(response)

if __name__ == "__main__":
    main()