# KortsteRouteTeam209.py  
# Soms ChatGPT gebruikt voor helpen met debuggen of voor vragen zoals "Hoe pas ik makkelijk een functie toe op elke waarde in een lijst?", dus vergelijkbaar met het gebruik van Stack Overflow of documentatie.

import turtle
import time
import json

TIMESTRAIGHT = 2.4    # tijd nodig om 1 vak vooruit te rijden
TIMETURN = 3.0       # tijd nodig om binnen 1 vak een 90 graden te draaien
TIMEPICKUP = 1.0    # tijd nodig om 1 groen torentje op te pakken

ACCEPT = 'accept'
ABANDON = 'abandon'
CONTINUE = 'continue'

# INITIALISATIE

def initiate_board(nbRows,nbCols):
    """
    De functie maakt een nieuw leeg bord aan met nbRows rijen en nbCols kolommen.

    Het bord is een matrix bestaande uit nbRows rijen en nbCols kolommen. Elk vakje bevat telkens een spatie
    (" ") om aan te duiden dat het vakje leeg is.

    Deze functie geeft het bord terug.
    Wanneer er een ongeldige invoer is (nbRows is < 1, nbCols is < 1),
    wordt 'None' teruggegeven.
    """
    if nbRows < 1 or nbCols < 1:
        return None

    board = []

    for i in range(nbRows):
        board.append([])
        for j in range(nbCols):
            board[i].append(" ")

    return board

def putGreen(board,x,y):
    """
        De functie plaatst een groen schijfje , een "G", op het bord op rijcoordinaat x en kolomcoordinaat y.

        De functie geeft het bord terug, met op de gegeven coordinaten de letter "G" om aan te geven dat hier
        een groen schijfje ligt.

        Indien x of y niet overeenkomt met de dimensies van het bord, zal het bord ongewijzigd gelaten worden.
    """

    if x < 0 or x >= len(board) or y < 0 or y >= len(board[0]):
        #print("x,y buiten range", x, y, len(board), len(board[0]))
        return board

    board[x][y] = "G"

    return board


def putRed(board, x, y):
    """
        De functie plaatst een rood schijfje op het bord op rijcoordinaat x en kolomcoordinaat y.

        De functie geeft het bord terug, met op de gegeven coordinaten de letter "R" om aan te geven dat hier
        een rood schijfje ligt.

        Indien x of y niet overeenkomt met de dimensies van het bord, zal het bord ongewijzigd gelaten worden.
    """
    
    if x < 0 or x >= len(board) or y < 0 or y >= len(board[0]):
        #print("x,y buiten range", x, y, len(board), len(board[0]))
        return board

    board[x][y] = "R"

    return board



###################################################################################################################
############# HULP-FUNCTIES ######################################################################################
###################################################################################################################

def getGreens(board):
    """
        De functie geeft een set terug met de posities van alle groene schijfjes van het bord
    """

    output = set()

    for i in range(len(board)):
        for j in range(len(board[0])):
            if board[i][j] == "G":
                output.add((i,j))

    return output

def getReds(board):
    """
        De functie geeft een set terug met de posities van alle rode schijfjes van het bord
    """
    
    output = set()

    for i in range(len(board)):
        for j in range(len(board[0])):
            if board[i][j] == "R":
                output.add((i,j))

    return output


def getLegalNeighbours(board,pos):
    """
        De functie geeft een set terug met alle toegestane posities waar een wagentje naar toe kan
        bewegen vanuit de gegeven positie 'pos'. De functie houdt daarbij rekening met de randen van het bord en
        de posities waar er zich een rood schijfje bevindt.
    """

    output = set()
    x, y = pos
    max_x = len(board)
    max_y = len(board[0])

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    for dx, dy in directions:
        new_x = x + dx
        new_y = y + dy

        if 0 <= new_x < max_x and 0 <= new_y < max_y and board[new_x][new_y] != "R":
            output.add((new_x, new_y))

    return output

def calculateTime(route):
    """
        De functie berekent de tijd die het wagentje nodig heeft om de gegeven route te rijden. De functie gebruikt
        hiervoor de constanten TIMESTRAIGHT en TIMETURN.

        Je mag ervan uitgaan dat het wagentje op de startpositie van de route de juiste orientatie bevat en niet meer
        hoeft te draaien om de eerste stap te zetten.

        Je mag ervan uitgaan dat route een geldige route is, zijnde een lijst van tupels die de achtereenvolgende coordinaten
        bevat waar het wagentje zich stap voor stap bevindt.
    """

    output = 0
    prev = route[0]
    prev_direction = 0
    direction = 0 # 0 = up, 1 = right, 2 = down, 3 = left
    straight = [(-1, 0), (0, 1), (1, 0), (0, -1)]

    if len(route) <= 0:
        return 0
    
    if route[0][0] == route[1][0]:
        if route[0][1] < route[1][1]:
            direction = 1
        else:
            direction = 3
    else:
        if route[0][0] < route[1][0]:
            direction = 2
        else:
            direction = 0

    #print(direction, "direction")
    #print(straight[direction], "straight", (prev + straight[direction]), "prev + straight[direction]")
    
    for i, pos in enumerate(route):
        if pos == prev:
            #print(f"+0, totaal: {output}")
            continue
        if pos == (prev[0] + straight[direction][0], prev[1] + straight[direction][1]):
            output += TIMESTRAIGHT
            #print(f"+{TIMESTRAIGHT} (straight), totaal: {output}")
        else:
            prev_direction = direction
            if prev[0] == route[i][0]:
                if prev[1] < route[i][1]:
                    direction = 1
                else:
                    direction = 3
            else:
                if prev[0] < route[i][0]:
                    direction = 2
                else:
                    direction = 0
            turn_steps = min(abs(prev_direction - direction), 4 - abs(prev_direction - direction))
            output += TIMESTRAIGHT + (TIMETURN*turn_steps)
            #print(f"+{TIMESTRAIGHT + (TIMETURN*turn_steps)} (turn + straight), totaal: {output}")
        prev = pos
        
    return output

# Geeft alleen posities en oppakken info, geen draaibewegingen, dus wordt niet gebruikt
def makeInstructionfile(route, board):
    """
        De functie genereert een .txt-bestand dat kan gebruikt worden je wagentje de opgegeven route te laten rijden op het
        opgegeven board.

        Elke regel van het bestand drie met een komma van elkaar gescheiden waarden, namelijk:
        rijnummer, kolomnummer, True/False
        waarbij de derde waarde een boolean is die aangeeft of er op de gegeven positie een groen schijfje dient opgepikt
        te worden.

        De functie gaat ervan uit dat "route" een geldige route is voor het opgegeven "board".
    """
    file = open('instructions.txt','w')
    for pos in route:
        pickup = "False"
        if board[pos[0]][pos[1]] == "G":
            pickup = "True"
        outputstring = str(pos[0])+", "+str(pos[1]) +", " + pickup + "\n"
        file.write(outputstring)
    file.close()

# Geeft ook draaibewegingen
def makeInstructionfile2(route, board, start_direction=1):
    if len(route) <= 1:
            return
    
    outputstring = ""
    prev = route[0]
    direction = start_direction # 0 = up, 1 = right, 2 = down, 3 = left
    straight = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    
    collected_greens = set() # groene torentjes die al zijn opgepakt bijhouden

    file = open('instructions.txt','w')
    for curr in route[1:]:
        dx = curr[0] - prev[0]
        dy = curr[1] - prev[1]

        try:
            target_direction = straight.index((dx, dy))
        except ValueError:
            raise ValueError(f"!!! Error !!!: Onmogelijke stap, van {prev} naar {curr}")

        turn_steps = (target_direction - direction) % 4

        if turn_steps == 1:
            outputstring += "R\n"
        elif turn_steps == 2:
            outputstring += "T180\n"
            #outputstring += "L\nL\n"
        elif turn_steps == 3:
            outputstring += "L\n"

        outputstring += "F\n"
        if board[curr[0]][curr[1]] == "G" and (curr[0], curr[1]) not in collected_greens:
            outputstring += "P\n"
            collected_greens.add((curr[0], curr[1]))

        direction = target_direction

        prev = curr
    outputstring += "S"
    file.write(outputstring)
    file.close()

# info voor website
def makeWebsiteFile(route, board):
    data = {}
    
    # diemensies van het bord
    data['dimensions'] = {
        'rows': len(board),
        'cols': len(board[0])
    }
    
    # hele bord
    data['board'] = []
    for row in board:
        data['board'].append(['G' if cell == 'G' else 'R' if cell == 'R' else ' ' for cell in row])
    
    # groene torentjes die al zijn opgepakt
    collected_greens = set()
    
    # route met oppakken info (maar nog zonder juiste orientatie) // uiteindelijk niet gebruikt
    data['route'] = []
    for pos in route:
        is_pickup = board[pos[0]][pos[1]] == 'G' and pos not in collected_greens
        if is_pickup:
            collected_greens.add(pos)
            
        data['route'].append({
            'row': pos[0],
            'col': pos[1],
            'pickup': is_pickup
        })
    
    collected_greens = set()
    
    # instructies (met draaibewegingen)
    data['instructions'] = []
    prev = route[0]
    direction = 1  # 0 = up, 1 = right, 2 = down, 3 = left
    straight = [(-1, 0), (0, 1), (1, 0), (0, -1)]
    
    for curr in route[1:]:
        dx = curr[0] - prev[0]
        dy = curr[1] - prev[1]
        
        target_direction = straight.index((dx, dy))
        turn_steps = (target_direction - direction) % 4
        
        if turn_steps == 1:
            data['instructions'].append({'action': 'R'})
        elif turn_steps == 2:
            data['instructions'].append({'action': 'T180'})
        elif turn_steps == 3:
            data['instructions'].append({'action': 'L'})
        
        data['instructions'].append({'action': 'F', 'row': curr[0], 'col': curr[1]})
        
        if board[curr[0]][curr[1]] == "G" and curr not in collected_greens:
            data['instructions'].append({'action': 'P'})
            collected_greens.add(curr)
        
        direction = target_direction
        prev = curr
    
    data['instructions'].append({'action': 'S'})
    
    # JSON bestand
    with open('website.json', 'w') as file:
        json.dump(data, file, indent=2)

###################################################################################################################
############# BACKTRACKING - sub-optimaal #########################################################################
###################################################################################################################

# In deze variant mag je gebruik maken van de functie 'fastestRoute' die alvast de snelste
# route tussen twee willekeurige posities op het bord bepaalt.
# Gebruik makend van deze functie kan je zelf de snelste route bepalen waarmee alle groene schijfjes
# kunnen opgepikt worden door deze route te interpreteren als een aaneenschakeling van snelste routes tussen twee
# groene schijfjes onderling.
# Let wel, dit algoritme geeft niet altijd de juiste oplossing voor de 'totale' snelste route, omdat het geen rekening
# houdt met de eventuele draaitijden op de vakjes waar groene schijfjes liggen.

MAX_PATH_LENGTH = 11 # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

def examine_help(finish, x, y):
    """
        examine-functie voor de 'fastestRoute'-backtracking.
    """

    if x == finish[0] and y == finish[1]:
        return "ACCEPT"
    
    return "CONTINUE"

def extend_help(board, x, y):
    """
        extend-functie voor de 'fastestRoute'-backtracking.
    """

    extended_solutions = [i for i in getLegalNeighbours(board, (x, y))]

    return extended_solutions


def solve_help(board, finish, x, y, route=None):
    """
        solve-functie voor de 'fastestRoute'-backtracking.
    """
    if route == None:
        route = []
    
    new_route = route + [(x, y)]
    #print("x:", x, "y:", y, "route:", new_route)
    if len(new_route) > MAX_PATH_LENGTH:
        return []

    exam = examine_help(finish, x, y)

    if exam == "ACCEPT":
        return [new_route]
    
    routes = []
    if exam == "CONTINUE":
        extended_solutions = extend_help(board, x, y)
        for extended_partial_solution in extended_solutions:
            
            result = solve_help(board, finish, extended_partial_solution[0], extended_partial_solution[1], new_route)
            routes.extend(result)
            '''if result != None:
                return result
            '''

    return routes

def fastestRoute(board, start, finish):
    """
        De functie geeft de snelste route terug  om van de positie 'start' naar de positie 'finish' te rijden op
        het gegeven bord. De route vermijdt daarbij de posities waar rode schijfjes aanwezig zijn.

        Je mag ervan uitgaan dat start en finish beiden tupels zijn met een x- en een y-coordinaat die de dimensies
        van het gegeven bord respecteren.

        Dit zal Prof. Holvoet samen met jullie bekijken in de les in semesterweek 9.
    """

    routes = solve_help(board, finish, start[0], start[1])

    if not routes:
        return None

    fastest_route = min(routes, key=calculateTime)
    return fastest_route


def collect(board,start,finish):
    """
        Deze functie geeft de snelste route terug om van de positie 'start' naar de positie 'finish' te rijden op
        het gegeven bord, waarbij de posities van alle groene schijfjes onderweg worden aangedaan door de route.

        Deze functie maakt gebruik van de hulpfunctie 'fastestRoute' en berekent de snelste route als een
        aaneenschakeling van snelste routes tussen twee groene schijfjes onderling.

        De functie houdt geen rekening met eventuele draaitijden die het wagentje nodig heeft om op de plek van het
        groene schijfje zelf eventueel van richting te veranderen.
    """

    def generate_permutations(items):
        if len(items) <= 1:
            return [items]
        perms = []
        for i in range(len(items)):
            rest = items[:i] + items[i+1:]
            for p in generate_permutations(rest):
                perms.append([items[i]] + p)
        return perms

    shortest_path = None
    shortest_length = float('inf')

    greens = list(getGreens(board))  # getGreens geeft een set terug, dus moet worden omgezet naar een lijst
    total_permutations = len(list(generate_permutations(greens)))

    for index, perm in enumerate(generate_permutations(greens), 1):
        if index % 100 == 0 or index == total_permutations:
            #print(f"Checking permutation {index}/{total_permutations} ({index/total_permutations*100:.2f}% complete)") # om progress bij te houden
            pass

        path = [start] + perm + [finish]
        total_route = []
        valid = True
        for i in range(len(path) - 1):
            if path[i] != path[i + 1]:
                segment = fastestRoute(board, path[i], path[i + 1])
                if segment is None:
                    valid = False
                    break
            else:
                segment = [path[i]]  # Geen route nodig als de begin- en eindpunt dezelfde zijn
            if i > 0:
                if segment is None or len(segment) == 0:
                    valid = False
                    break
                segment = segment[1:]
            total_route.extend(segment)
        if not valid:
            continue
        time = calculateTime(total_route)
        if time < shortest_length:
            shortest_length = time
            shortest_path = total_route

    print(f"Shortest path found with length: {shortest_length + len(greens)*TIMEPICKUP}")
    return shortest_path

# (Extra)functie om het bord en de route grafisch te tekenen (grotendeels door AI geschreven)
def showShortestPath(board, route):
    """
    Teken het speelveld en de kortste route grafisch met behulp van Turtle.
    
    - Het bord wordt als een rooster getekend.
    - Groene en rode schijfjes worden in hun cel getoond.
    - De route wordt getekend als een blauwe lijn tussen de cellen.
    """
    cell_size = 50
    nrows = len(board)
    ncols = len(board[0]) if nrows > 0 else 0

    # Setup turtle screen
    screen = turtle.Screen()
    # Zorg dat het scherm groot genoeg is voor het rooster
    screen.setup(width=800, height=600)
    screen.title("Kortste Route Weergave")
    
    t = turtle.Turtle()
    t.speed(0)
    t.hideturtle()

    # Teken het rooster
    for i in range(nrows):
        for j in range(ncols):
            # Bepaal de coordinaten zodat het rooster gecentreerd is:
            x = j * cell_size - (ncols * cell_size) / 2
            y = (nrows * cell_size) / 2 - i * cell_size
            t.penup()
            t.goto(x, y)
            t.pendown()
            # Teken de vier zijden van de cel
            for _ in range(2):
                t.forward(cell_size)
                t.right(90)
                t.forward(cell_size)
                t.right(90)
            # Als de cel een groen of rood schijfje bevat, schrijf dit in het midden
            if board[i][j] != " ":
                t.penup()
                cx = x + cell_size / 2
                cy = y - cell_size / 2 - 10  # lichte aanpassing voor de tekst
                t.goto(cx, cy)
                if board[i][j] == "R":
                    t.color("red")
                elif board[i][j] == "G":
                    t.color("green")
                else:
                    t.color("black")
                t.write(board[i][j], align="center", font=("Arial", 16, "normal"))
                t.color("black")

    # Teken de route: verondersteld is dat route een lijst is met (rij, kolom) posities.
    if route:
        t.shape("arrow")
        t.penup()
        t.color("blue")
        t.width(3)
        # Zet de turtle op het centrum van de startcel:
        start_row, start_col = route[0]
        start_x = start_col * cell_size - (ncols * cell_size) / 2 + cell_size / 2
        start_y = (nrows * cell_size) / 2 - start_row * cell_size - cell_size / 2
        t.goto(start_x, start_y)
        t.showturtle()
        t.speed(1)
        t.pendown()
        # Teken lijnen naar de volgende cellen
        for pos in route:
            row, col = pos
            cx = col * cell_size - (ncols * cell_size) / 2 + cell_size / 2
            cy = (nrows * cell_size) / 2 - row * cell_size - cell_size / 2
            #t.pencolor(0, min(1, row * 0.2), min(1, col * 0.1))
            t.setheading(t.towards(cx, cy))
            t.goto(cx, cy)
            time.sleep(0.05)
    
    # Houd het venster open totdat het wordt gesloten
    screen.exitonclick()




if __name__ == "__main__":

    # board = initiate_board(int(input("Geef aantal rijen: ")), int(input("Geef aantal kolommen: ")))
    board = initiate_board(4, 6)
    
    putGreen(board, 3, 0)
    putGreen(board, 3, 1)
    putGreen(board, 3, 4)
    putGreen(board, 0, 3)
    putGreen(board, 0, 5)
    putGreen(board, 3, 5)
    putRed(board, 0, 1)
    putRed(board, 2, 5)
    putRed(board, 3, 2)
    putRed(board, 3, 3)
    
    print(board)
    '''
    #vraag voor posities van groene schijfjes (-1 = stoppen met invoer)
    print("Geef rij en kolom voor groene schijfjes (-1 = stoppen met invoer)")
    while True:
        rij = int(input("Geef rij: "))
        if rij == -1:
            break
        kolom = int(input("Geef kolom: "))
        if kolom == -1:
            break
        putGreen(board, rij, kolom)
        print(board)
    print("Geef rij en kolom voor rode schijfjes (-1 = stoppen met invoer)")
    #vraag voor posities van rode schijfjes (-1 = stoppen met invoer)
    while True:
        rij = int(input("Geef rij: "))
        if rij == -1:
            break
        kolom = int(input("Geef kolom: "))
        if kolom == -1:
            break
            
        putRed(board, rij, kolom)
        print(board)
    '''

    #print("route:", solve_help(board, (1, 3), 0, 0))
    beste_route = collect(board,(0,0),(0,0))
    makeInstructionfile2(beste_route, board)
    makeWebsiteFile(beste_route, board)
    input("toon (druk op enter):")
    showShortestPath(board, beste_route)