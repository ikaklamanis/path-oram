from random import randint
import pprint
import matplotlib.pyplot as plt
import math

class staticBST:
    def __init__(self, N):
        self.nodes = [None for _ in range(N)]
    
    def insert(self, key, data):
        self.nodes[key] = data
    
    def getLeaf(self, leafNum):
        pass

class Block:
    def __init__(self):
        ## dummy block
        self.id = -1
        self.leaf = -1
        self.data = 0

    def __str__(self):
        return "Block id: " + str(self.id) + " data: " + str(self.data)

class Bucket:
    def __init__(self):
        self.blocks = None

    def __str__(self):
        s = "\n"
        for block in self.blocks:
            s += str(block) + "\n"
        return s

class Node:
    def __init__(self):
        self.parent = None
        self.left = None
        self.right = None
        self.key = None

        self.start = None
        self.end = None
        self.height = None

        self.bucket = None

    def isLeaf(self):
        return self.left is None and self.right is None


class PathORAM():
    ####
    # N: total number of blocks
    # L: binary tree height
    # B: block size
    # Z: bucket size
    def __init__(self, L = 4, B = 32, Z = 4):
        self.height = L
        self.blockSize = B
        self.bucketSize = Z

        self.start = 0
        self.end = 2 ** L - 1
        self.root = self.build_tree(self.start, self.end, self.height)

    def build_tree(self, start, end, height):
        node = Node()
        node.start = start
        node.end = end
        node.height = height

        if start == end:
            assert height == 0
            key = start
            node.start = key
            node.end = key
            node.key = key
        else:
            node.left = self.build_tree(start, (start + end) // 2, height - 1)
            node.right = self.build_tree((start + end) // 2 + 1, end, height - 1)
            node.left.parent = node
            node.right.parent = node

        bucket = Bucket()
        bucket.blocks = [Block() for _ in range(self.bucketSize)]
        node.bucket = bucket
        
        return node
    

    def getLeaf(self, key):
        # print("getLeaf for key", key)
        node = self.root
        while node:
            # print("node start", node.start, "node end", node.end)
            if key == node.start and key == node.end:
                assert node.isLeaf(), "node is not a leaf"
                return node
            if key <= (node.start + node.end) // 2:
                node = node.left
            else:
                node = node.right
        return None
    
    def readBucket(self, leafKey, level):
        # print("reading bucket at level", level)
        leaf = self.getLeaf(leafKey)
        assert leaf is not None
        node = leaf
        for _ in range(self.height - level):
            node = node.parent
        # print("found bucket at level", level)
        # print("height of node", node.height)
        assert node.height == self.height - level

        return node.bucket
    
    def readAllBuckets(self, leafKey):
        # print("reading all buckets for leaf", leafKey)
        buckets = []
        leaf = self.getLeaf(leafKey)
        assert leaf is not None
        node = leaf
        # print("traversing up the tree")
        # print("node start", node.start, "node end", node.end)
        buckets.append(node.bucket)
        node = node.parent
        for _ in range(self.height):
            # print("node start", node.start, "node end", node.end)
            buckets.append(node.bucket)
            node = node.parent
        assert node is None
        return buckets
    
    def writeBucket(self, leafKey, level, bucket):
        # print("writing bucket at level", level)
        leaf = self.getLeaf(leafKey)
        assert leaf is not None
        node = leaf
        # print("traversing up the tree")
        # print("node start", node.start, "node end", node.end)
        for _ in range(self.height - level):
            # print("node start", node.start, "node end", node.end)
            node = node.parent
        # print("found node at level", level)
        # print("height of node", node.height)
        assert node.height == self.height - level
        node.bucket = bucket





class Client:
    def __init__(self, L = 4, N = 10, Z = 4, B = 32):

        self.L = L
        self.N = N
        self.Z = Z

        self.poram = PathORAM(L, B, Z)

        self.db = {i : 0 for i in range(N)}
        self.position_map = [randint(0, 2 ** L - 1) for _ in range(N)]
        self.stash = set()

        self.doInitialWrites()


    def findBlockInStash(self, a):
        for block in self.stash:
            if block.id == a:
                return block
        return None
    
    def replaceBlockInStash(self, a, new_data):
        for block in self.stash:
            if block.id == a:
                block.data = new_data
                return True
        return False
    
    def doInitialWrites(self):
        print("--------------doInitialWrites--------------")
        for a in range(self.N):
            x = self.position_map[a]
            # print("--------writing block", a, "at path starting at leaf", x, "--------")
            data = self.db[a]
            buckets = self.poram.readAllBuckets(leafKey = x)
            placed = False
            for h in range(len(buckets)):
                bucket = buckets[h]
                # print("bucket before", bucket)
                for block in bucket.blocks:
                    if block.id == -1:
                        block.id = a
                        block.data = data
                        placed = True
                        break
                if placed:
                    # print("bucket after", bucket)
                    self.poram.writeBucket(leafKey = x, level = self.L - h, bucket = bucket)
                    break
            assert placed, "could not place block in any bucket"



    def access(self, op, a, new_data = None):
        assert a <= self.N - 1
        x = self.position_map[a]
        # print("----------accessing block", a, "at position", x, "----------")
        self.position_map[a] = randint(0, 2 ** self.L - 1)
        # print("new position for block", a, "is", self.position_map[a])

        buckets = self.poram.readAllBuckets(leafKey = x)
        for bucket in buckets:
            for block in bucket.blocks:
                if block.id != -1:
                    self.stash.add(block)

        block = self.findBlockInStash(a)
        # print("block found in stash", block)
        assert block is not None
        if op == "write":
            self.replaceBlockInStash(a, new_data)

        def lca(u, v):
            u_bin = format(u, f'0{self.L}b')
            v_bin = format(v, f'0{self.L}b')
            if u == v:
                return self.L
            lca_level = 0
            for i in range(L):
                # print("i", i, "u_bin[i]", u_bin[i], "v_bin[i]", v_bin[i])
                if u_bin[i] != v_bin[i]:
                    lca_level = i
                    break
            return lca_level
        
        removed_from_stash = 0
        for l in range(self.L, -1, -1):
            s_prime = []
            for _block in self.stash:
                if lca(x, self.position_map[_block.id]) == l:
                    s_prime.append(_block)
            # print(f"s_prime at level {l} has size {len(s_prime)}")
            bucket_size = min(self.poram.bucketSize, len(s_prime))
            bucket = Bucket()
            bucket.blocks = s_prime[:bucket_size]
            for _ in range(bucket_size, self.poram.bucketSize):
                bucket.blocks.append(Block())
            # print("bucket at level", l, "has size", len(bucket.blocks))
            # print("stash size before removal", len(self.stash))
            for _block in s_prime[:bucket_size]:
                assert _block in self.stash, "block not in stash"
            self.stash = self.stash - set(s_prime[:bucket_size])
            # print("stash size after removal", len(self.stash))
            # print("should have removed", min(bucket_size, len(s_prime)))
            self.poram.writeBucket(leafKey = x, level = l, bucket = bucket)
            removed_from_stash += bucket_size
        # print("removed from stash", removed_from_stash)

        return block




def simulate(L, N, Z, total_runs = 1_000, warmup_runs = 100):
    print("starting simulation for L = ", L, " and Z = ", Z)
    sim_file = f"simulation_L_{L}_Z_{Z}.txt"
    f = open(sim_file, "w")
    sim_runs = total_runs - warmup_runs
    # f.write(f"L = {L}, N = {N}, Z = {Z}, total_runs = {total_runs}, warmup_runs = {warmup_runs}\n")
    f.write(f"-1, {sim_runs}\n")
    client = Client(L, N, Z)

    stash_sizes = []

    for i in range(total_runs):
        if i % (2**16) == 0:
            print(f"run # {i}")
        id = i % N
        op = "read"
        # print("stash size before", len(client.stash))
        block = client.access(op, id)
        # print(f"block {id}", block)
        assert id == block.id
        stash_size = len(client.stash)
        # print("stash size after:", stash_size)
        if i >= warmup_runs:
            stash_sizes.append(stash_size)
    print("simulation complete")
    print("max stash size", max(stash_sizes))

    max_stash_size = max(stash_sizes)
    freqs = {}
    for i in range(len(stash_sizes)):
        if stash_sizes[i] not in freqs:
            freqs[stash_sizes[i]] = 0
        freqs[stash_sizes[i]] += 1
    for s in range(0, max_stash_size + 1):
        if s not in freqs:
            freqs[s] = 0
    
    # print("freqs")
    # pp.pprint(freqs)
    
    keys = sorted(list(freqs.keys()))
    L = len(keys)
    gtFreqs = {}
    gtFreqs[keys[L-1]] = 0
    for i in range(L-2, -1, -1):
        gtFreqs[keys[i]] = gtFreqs[keys[i+1]] + freqs[keys[i+1]]
    # print("gtFreqs")
    # pp.pprint(gtFreqs)
    
    for key in sorted(list(gtFreqs.keys())):
        f.write(f"{key}, {gtFreqs[key]}\n")
    f.close()

    return gtFreqs




def plot_simulation(gtFreqs, num_accesses):
    step = 1

    # Create a list of indices for the x-axis
    x = sorted(gtFreqs.keys())
    x = x[:len(x) - 1]
    print("x", x)   
 
    y = [] 
    for key in x:
        try:
            y.append(math.log(num_accesses / gtFreqs[key]))
        except:
            print("division by zero for key", key, "gtFreqs[key]", gtFreqs[key])
            return

    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.scatter(x, y, marker='o', linestyle='-', color='b', label='hello', s=10)

    # Add titles and labels
    plt.title('Stash size statistics')
    plt.xlabel('R')
    plt.ylabel('log(1/delta(R))')
    # Limit x-ticks to every 5th index for clarity
    # plt.xticks(x[::step * 10])  # Adjust the step as needed (e.g., 5 or 10)
    # Add grid
    plt.grid()
    # Add a legend
    plt.legend()

    # Show the plot
    plt.show()


def plot_all_simulations(L, N, Z_values, num_accesses):
    # Create the plot
    plt.figure(figsize=(10, 6))

    colors = ['b', 'g', 'r', 'c', 'm', 'y', 'k', 'w']
    for i in range(len(Z_values)):
        Z = Z_values[i]
        sim_file = f"simulation_L_{L}_Z_{Z}.txt"
        f = open(sim_file, "r")
        lines = f.readlines()
        f.close()
        gtFreqs = {}
        for line in lines[1:]:
            key, value = line.strip().split(", ")
            gtFreqs[int(key)] = int(value)
        
        step = 1

        # Create a list of indices for the x-axis
        x = sorted(gtFreqs.keys())
        x = x[:len(x) - 1]
        # print("x", x)   
    
        y = [] 
        for key in x:
            try:
                y.append(math.log(num_accesses / gtFreqs[key]))
            except:
                print("division by zero for key", key, "gtFreqs[key]", gtFreqs[key])
                return

        plt.scatter(x, y, marker='o', linestyle='-', color=colors[i], label=f"Z={Z}", s=10)

    plt.title('Stash size statistics')
    plt.xlabel('R')
    plt.ylabel('log(1/delta(R))')
    # Limit x-ticks to every 5th index for clarity
    # plt.xticks(x[::step * 10])  # Adjust the step as needed (e.g., 5 or 10)
    plt.grid()
    plt.legend()

    fig_file = f"stash_size_plot_Z_values_" + "_".join([str(Z) for Z in Z_values]) + ".png"
    plt.savefig(fig_file, dpi=300, bbox_inches='tight')

    # plt.show()



if __name__ == '__main__':

    pp = pprint.PrettyPrinter(indent=4)

    L = 20
    N = 2 ** L 
    total_runs = 10_000
    warmup_runs = 1_000
    sim_runs = total_runs - warmup_runs


    Z_values = [4, 6]
    for Z in Z_values:
        _gtFreqs = simulate(L, N, Z, total_runs, warmup_runs)
    plot_all_simulations(L, N, Z_values, sim_runs)

    Z_values = [2]
    for Z in Z_values:
        _gtFreqs = simulate(L, N, Z, total_runs, warmup_runs)
    plot_all_simulations(L, N, Z_values, sim_runs)
    