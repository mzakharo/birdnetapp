import sys, os

def cleanup(folder, keep_files):
    for x in os.walk(folder):
        files = x[2]
        if not(len(files)):
            continue
        files = sorted(files, reverse=True)
        for file in files[keep_files:]:
            fname = os.path.abspath(os.path.join(x[0], file))
            print("Cleanup removing:", fname)
            try:
                os.unlink(fname)
            except OSError:
                print("Unable to remove", fname)

if __name__ == '__main__':
    cleanup(sys.argv[1], int(sys.argv[2]))
