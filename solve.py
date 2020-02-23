import json

# A piece is either three (short) or four beads (long).  It can be places in
# exactly two ways (ignoring translations and planar rotations).  For instance,
# the yellow piece is either
#
#    x x x x          x
#        x x    or    x x x x
#
# We call this the two variants of the yellow piece: A and B.  We represent
# it below with the string "x..." + "..xx".  (The "xxxx" is implicit.)
PIECES = {
        'yellow':      'x...'
                       '..xx',
        'blue':        'x.x.'
                       'x...',
        'orange':      '..x.'
                       'x.x.',
        'red':         'x..x'
                       'x...',
        'pink':        '.x..'
                       'xx..',
        'light-blue':  '.xx.'
                       '.x..',
        'light-green': 'x.x'
                       'x..',
        'dark-green':  '.x.'
                       'xx.',
        'purple':      'x..'
                       'oxx',
        'dark-blue':   'x.x'
                       '.x.',

}

# We represent a piece-on-the-board "mask" by a 50-bit number with LSB to MSB
# going left to right top to bottom, for instance
#
#   . x . . . . . . . . .
#   . x x x x . . . . . .
#   . . . . . . . . . . .
#   . . . . . . . . . . .
#   . . . . . . . . . . .
#
# is represented by 2 + 2^11 + 2^12 + 2^13 + 2^14.

FULL_BOARD = 2**50-1

# A piece as it is, is called the N (for north) variant.  Rotated 90 degrees
# clockwise is E (for east); 180 CW is S (south) and finally 270 CW is W
# (for west).

# We represent a move by the quintuplet 
#   (<name-of-piece>, <variant>, <rotation>, <x-offset>, <y-offset>)

def parse_piece_description(desc):
    length = len(desc) // 2
    maskA, maskB = 0, 0
    for i in range(length):
        if desc[i] == 'x':
            maskA += 2**i
        maskA += 2**(i+10)
        maskB += 2**i
        if desc[i+length] == 'x':
            maskB += 2**(i+10)
    return maskA, maskB, length

def print_mask(mask):
    r = ''
    for y in range(5):
        for x in range(10):
            if 2**(10*y+x) & mask:
                r += 'x '
            else:
                r += '. '
        r += '\n'
    print(r)



# Computes all possible moves for the pieces.
def compute_moves():
    # Main course, compute the moves
    moves = []
    for name, desc in PIECES.items():
        per_piece = []
        maskA, maskB, length = parse_piece_description(desc)
        masks = (
            compute_rotations(maskA, length),
            compute_rotations(maskB, length)
        )
        for rotIdx, rot in enumerate('NESW'):
            for varIdx, var in enumerate('AB'):
                if rot in 'NS':
                    max_x = 11 - length
                    max_y = 4
                else:
                    max_x = 9
                    max_y = 6 - length
                for x in range(max_x):
                    for y in range(max_y):
                        mask = masks[varIdx][rotIdx] * 2**(x + 10*y)
                        popcnt = bin(mask).count('1')
                        per_piece.append(((name, var, rot, x, y), mask, popcnt))
        moves.append(per_piece)

    # Dolce, create a position to move look-up-table
    posLut = {}
    for x in range(10):
        for y in range(5):
            b = 2**(10*y+x)
            posLut[x,y] = []
            for rnd in range(10):
                masks = []
                for move, mask, beads in moves[rnd]:
                    if mask & b:
                        masks.append(mask)
                posLut[x,y].append(masks)

    return moves, posLut


# Computes the four rotations of a given variant of a piece
def compute_rotations(mask, length):
    east, south, west = 0, 0, 0

    for y in range(2):
        for x in range(length):
            if 2**(10*y+x) & mask:
                south += 2**(10*(1-y)+(length-x-1))
                east += 2**(10*x+(1-y))
                west += 2**(10*(length-x-1)+y)

    return mask, east, south, west


class Frame():
    def __init__(self, board, movesDone, piecesTodo, cellsFree):
        self.board = board
        self.movesDone = movesDone
        self.piecesTodo = piecesTodo
        self.cellsFree = cellsFree


# SKIP_PIECES = ['yellow', 'light-green']
# START_BOARD = ('..........'
#                '..x..xx...'
#                '..x..xxxx.'
#                '..xx......'
#                '..........')
# INIT_MASK = sum([2**i if b == 'x' else 0 for  i, b in enumerate(START_BOARD)])
# INIT_BEADS = START_BOARD.count('x')
SKIP_PIECES=[]
INIT_MASK=0
INIT_BEADS=0


def main():
    f = open('sols', 'w')
    sols = 0
    moves, posLut = compute_moves()
    stack = [Frame(
        board=INIT_MASK,
        movesDone=(),
        piecesTodo=10,
        cellsFree=50 - INIT_BEADS,
    )]
    iteration = 0
    while stack:
        iteration += 1
        frame = stack.pop()
        if iteration % 10000 == 0:
            print(iteration, len(stack), frame.cellsFree, sols)
        # print(frame.movesDone)
        # print_mask(frame.board)
        if moves[10-frame.piecesTodo][0][0][0] in SKIP_PIECES:
            stack.append(
                Frame(
                    board=frame.board,
                    movesDone=frame.movesDone,
                    piecesTodo=frame.piecesTodo - 1,
                    cellsFree=frame.cellsFree
                )
            )
            continue
        for move, mask, beads in moves[10-frame.piecesTodo]:
            if frame.board & mask:
                continue
            newAllowedMoves = []
            newBoard = frame.board | mask
            newCellsFree = frame.cellsFree - beads
            if (frame.piecesTodo-1) * 4 > newCellsFree:
                # print('a', len(frame.movesDone))
                # print_mask(newBoard)
                continue
            if (frame.piecesTodo-1) * 6 < newCellsFree:
                # print('b', len(frame.movesDone))
                # print_mask(newBoard)
                continue
            newMovesDone = frame.movesDone + (move,)
            if newCellsFree == 0:
                sols += 1
                json.dump(newMovesDone, f)
                f.write('\n')
                continue
                # print()
                # print('===================================================')
                # print()
                # for move, mask in frame.movesDone:
                #     print(move)
                #     print_mask(mask)
                #     print()
                # continue

            # Check if every empty cell still fits some piece
            ok = True
            for x in range(10):
                for y in range(5):
                    b = 2**(10*y+x)
                    if newBoard & b:
                        continue
                    ok2 = False
                    for rnd in range(10-frame.piecesTodo, 10):
                        for mask2 in posLut[x,y][rnd]:
                            if not (mask2 & newBoard):
                                ok2 = True
                                break
                        if ok2:
                            break
                    if not ok2:
                        # print('not ok', x, y)
                        # print_mask(newBoard)
                        ok = False
                        break
                if not ok:
                    break
            if not ok:
                continue

            stack.append(
                Frame(
                    board=newBoard,
                    movesDone=newMovesDone,
                    piecesTodo=frame.piecesTodo - 1,
                    cellsFree=newCellsFree,
                )
            )

    print("TOTAL NUMBER OF SOLUTIONS", sols)


if __name__ == '__main__':
    main()

