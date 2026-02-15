# SPDX-License-Identifier: Apache-2.0
from jcapy.config import get_active_library_path

def setup_recall(parser):
    parser.add_argument("query", nargs="+", help="Natural language query")

def setup_memorize(parser):
    parser.add_argument("--force", action="store_true", help="Clear memory before ingesting")
    parser.add_argument("--path", help="Specific path to ingest (file or dir)", default=None)

def run_recall(args):
    try:
        from jcapy.memory import get_memory_bank
        bank = get_memory_bank()
        # Check if local bank needs init
        if hasattr(bank, 'collection') and bank.collection.count() == 0:
            print(f"\033[1;33m🧠 Initializing Memory Bank (First Run)...\033[0m")
            bank.sync_library(get_active_library_path())

        query = " ".join(args.query)
        print(f"\033[1;36m🔍 Recalling knowledge related to: '{query}'...\033[0m")
        results = bank.recall(query, n_results=5)

        if not results:
            print(f"\033[0;90mNo relevant memories found.\033[0m")
        else:
            for i, res in enumerate(results, 1):
                meta = res['metadata']
                similarity = (1 - res['distance']) * 100
                print(f"\n{i}. \033[1m{meta.get('name', 'Unknown')}\033[0m ( Relevance: {similarity:.1f}% )")
                print(f"   Shape: {meta.get('source', 'Unknown')}")
    except ImportError:
         print(f"⚠️  Detailed error loading RemoteMemoryBank (check pinecone-client). Falling back to Local.")
    except Exception as e:
        print(f"\033[1;31mMemory Error: {e}\033[0m")

def run_memorize(args):
    try:
        from jcapy.memory import get_memory_bank
        bank = get_memory_bank()
        paths = [args.path] if args.path else [get_active_library_path()]

        print(f"\033[1;36m🧠 Memorizing Knowledge...\033[0m")
        if args.force:
            print(f"\033[1;33m  • Force Clean enabled.\033[0m")

        stats = bank.memorize(paths, clear_first=args.force)
        print(f"\n\033[1;32m✨ Update Complete:\033[0m")
        print(f"  • Added: {stats['added']}")
        print(f"  • Skipped: {stats['skipped']}")
        print(f"  • Errors: {stats['errors']}")
    except Exception as e:
        print(f"\033[1;31mMemorize Error: {e}\033[0m")
