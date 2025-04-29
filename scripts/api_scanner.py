import os
import re

def scan_api_calls(base_path, api_base_url):
    api_calls = set()
    pattern = re.compile(re.escape(api_base_url) + r'[^\'"\\s]+')

    for root, _, files in os.walk(base_path):
        for file in files:
            if file == "credentials.py":
                continue
            if file.endswith(('.py', '.js', '.ts', '.json', '.txt', '.html')):
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        for match in matches:
                            api_calls.add(match)
                except Exception as e:
                    print(f"Could not read file {file_path}: {e}")

    return sorted(api_calls)

def main():
    base_path = os.path.dirname(os.path.abspath(__file__)) + "/.."
    api_base_url = "http://radio.garden/api/"
    api_calls = scan_api_calls(base_path, api_base_url)

    output_file = os.path.join(base_path, "api_endpoints.txt")
    with open(output_file, 'w', encoding='utf-8') as f:
        for call in api_calls:
            f.write(call + "\n")

    print(f"Found {len(api_calls)} API calls. Results saved to {output_file}")

if __name__ == "__main__":
    main()
