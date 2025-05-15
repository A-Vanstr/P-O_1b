import { useState, useEffect, React } from "react";
import Cookies from "js-cookie"; // Import js-cookie
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Sun, Moon, ShieldCheck, Star, Hexagon, BringToFront, Boxes, CircleDot, Joystick, CircleArrowUp, ArrowUp, ArrowDown, RotateCw, RotateCcw, RefreshCw, Hand, Route, TimerOff } from "lucide-react";
import Image from "next/image";
import { cn } from "@/lib/utils";
import Autooo from '@/assets/auto2.svg';
import { useWebSocket } from "@/hooks/useWebSocket";
import LogViewer from "@/components/log-viewer";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion"
import { Separator } from "@/components/ui/separator"

const generateRandomPositions = (count, rows, cols) => {
    const positions = new Set();
    while (positions.size < count) {
      let x = Math.floor(Math.random() * (cols - 1)) + 1;
      let y = Math.floor(Math.random() * (rows - 1)) + 1;

      while (x === 1 && y === 1) {
        x = Math.floor(Math.random() * (cols - 1)) + 1;
        y = Math.floor(Math.random() * (rows - 1)) + 1;
      }
      positions.add(`${x},${y}`);
    }
    return Array.from(positions).map(pos => pos.split(",").map(Number));
  };

const BlockProgressBar = ({ pickedPucks }) => {
  const totalBlocks = 6;
  const filledBlocks = Math.min(pickedPucks.size, totalBlocks);

  return (
    <Card className="bg-white dark:bg-neutral-900 shadow-xl dark:shadow-[0px_4px_12px_rgba(255,255,255,0.03)] w-12 flex flex-col items-center">
      <CardContent className="flex flex-col-reverse gap-2 p-2 rounded-lg">
        {[...Array(totalBlocks)].map((_, index) => (
          <div
            key={index}
            className={cn(
              "w-8 h-6 rounded-md transition-all", 
              index < filledBlocks ? "bg-green-500 shadow-[0px_0px_6px_0px_rgba(0,255,0,0.6)]" : "shadow-[0px_2px_4px_0px_rgba(0,0,0,0.2)] bg-gray-200 dark:bg-neutral-800"
            )}
          />
        ))}
      </CardContent>
    </Card>
  );
};

export default function Dashboard() {
  const [timeLeft, setTimeLeft] = useState(300); // 5 minutes
  const [isRunning, setIsRunning] = useState(false);
  const [timerStarted, setTimerStarted] = useState(false);
  const [score, setScore] = useState(0);
  const [darkMode, setDarkMode] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isArmed, setIsArmed] = useState(false);
  const [position, setPosition] = useState({ top: 12, left: 9 });
  const [manualControl, setManualControl] = useState(false);
  const [boardData, setBoardData] = useState(null);
  const [instructionIndex, setInstructionIndex] = useState(0);
  const [currentCommand, setCurrentCommand] = useState("");
  const [pickedPucks, setPickedPucks] = useState(new Set());
  const [instructionsStarted, setInstructionsStarted] = useState(false);
  const [posX, setPosX] = useState(1);
  const [posY, setPosY] = useState(1);
  const [direction, setDirection] = useState("right");
  const [rotationAngle, setRotationAngle] = useState(90);
  const [logs, setLogs] = useState([]);
  
  // All state hooks above, custom hooks below
  const { sendCommand, messages, ws, isConnected } = useWebSocket(setScore, setInstructionIndex, setCurrentCommand);

  const gridRows = 5;
  const gridCols = 7;

  // Update robot position and handle instructions
  useEffect(() => {
    if (!timerStarted) return; // Only proceed if game has started
    if (boardData && boardData.instructions && boardData.instructions[instructionIndex]) {
      const instruction = boardData.instructions[instructionIndex];
      
      // Handle different instruction types
      switch (instruction.action) {
        case 'F':
          if (instruction.row !== undefined && instruction.col !== undefined) {
            setPosX(instruction.col + 1);
            setPosY(instruction.row + 1);
          }
          break;
        case 'L':
          setRotationAngle(prev => (prev - 90) % 360);
          setDirection(prev => {
            const directions = ["up", "left", "down", "right"];
            const currentIndex = directions.indexOf(prev);
            return directions[(currentIndex + 1) % 4];
          });
          break;
        case 'R':
          setRotationAngle(prev => (prev + 90) % 360);
          setDirection(prev => {
            const directions = ["up", "right", "down", "left"];
            const currentIndex = directions.indexOf(prev);
            return directions[(currentIndex + 1) % 4];
          });
          break;
        case 'T180':
          setRotationAngle(prev => (prev + 180) % 360);
          setDirection(prev => {
            const directions = ["up", "right", "down", "left"];
            const currentIndex = directions.indexOf(prev);
            return directions[(currentIndex + 2) % 4];
          });
          break;
        case 'P':
          setPickedPucks(prev => new Set([...prev, `${posY-1},${posX-1}`]));
          setScore(score + 100);
          break;
      }
    }
  }, [instructionIndex, boardData, timerStarted]);

  // Function to get readable command name
  const getCommandName = (cmd) => {
    switch(cmd) {
      case 'F': return 'Forward';
      case 'L': return 'Left Turn';
      case 'R': return 'Right Turn';
      case 'T180': return 'Turn 180°';
      case 'P': return 'Pick Up';
      case 'S': return 'Stop';
      default: return cmd || '';
    }
  };

  // Compute style for the robot so its center aligns with the grid intersection
  const robotStyle = {
    left: `${((posX / 7) * 100)+0.3}%`,
    top: `${((posY / 5) * 100)+0.5}%`,
    transform: `translate(-50%, -50%) rotate(${rotationAngle}deg)`,
    transition: "left 0.3s ease, top 0.3s ease, transform 0.2s ease-in-out",
  };
  

  useEffect(() => {
    const originalLog = console.log;
    const originalError = console.error;

    const captureLog = (type, args) => {
      setLogs(prevLogs => [...prevLogs, { message: args.join(" "), type }]);
    };

    console.log = (...args) => {
      captureLog("log", args);
      originalLog(...args);
    };

    console.error = (...args) => {
      captureLog("error", args);
      originalError(...args);
    };

    return () => {
      console.log = originalLog;
      console.error = originalError;
    };
  }, []);
  {/*
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (e.key === "ArrowUp") {
        sendCommand("forward");
        moveRobot("forward");
      } else if (e.key === "ArrowDown") {
        sendCommand("backward");
        moveRobot("backward");
      } else if (e.key === "ArrowLeft") {
        sendCommand("turnLeft");
        moveRobot("turnLeft");
      } else if (e.key === "ArrowRight") {
        sendCommand("turnRight");
        moveRobot("turnRight");
      }
    };
  
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);
  */}

  // Load board data from website.json
  useEffect(() => {
    fetch('/website.json')
      .then(response => response.json())
      .then(data => {
        setBoardData(data);
      })
      .catch(error => {
        console.error('Error loading board data:', error);
      });
  }, []);

  // Load dark mode preference from cookie on mount
  useEffect(() => {
    const savedMode = Cookies.get("darkMode"); // Read cookie
    if (savedMode === "true") {
      setDarkMode(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  useEffect(() => {
    let timer;
    if (timerStarted && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft((prev) => prev - 1);
      }, 1000);
    } else if (timeLeft === 0) {
      setIsRunning(false);
      setTimerStarted(false);
    }
    return () => clearInterval(timer);
  }, [timerStarted, timeLeft]);

  const startGame = () => {
    sendCommand("start");
    setIsRunning(true);
    setTimerStarted(true);
    setInstructionsStarted(true);
  };

  const stopRobot = () => {
    if (!isArmed) return;
    sendCommand("stop");
    console.log("Emergency Stop Activated!");
    setIsRunning(false);
  };
  

  const toggleDarkMode = () => {
    setDarkMode((prev) => {
      const newMode = !prev;
      Cookies.set("darkMode", newMode, { expires: 365 }); // Store for 1 year
      document.documentElement.classList.toggle("dark", newMode);
      return newMode;
    });
  };

  const moveRobot = (action) => {
    if (action === "turnRight" || action === "turnLeft") {
      const directionOrder = ["up", "right", "down", "left"];
      setDirection((prevDirection) => {
        const currentIndex = directionOrder.indexOf(prevDirection);
        const newIndex =
          action === "turnRight" ? (currentIndex + 1) % 4 : (currentIndex + 3) % 4;
    
        setRotationAngle((prevAngle) => {
          const currentAngleMod = ((prevAngle % 360) + 360) % 360;
          const desiredAngle = newIndex * 90;
          let diff = desiredAngle - currentAngleMod;
          if (diff > 180) diff -= 360;
          if (diff < -180) diff += 360;
          return prevAngle + diff;
        });
    
        return directionOrder[newIndex];
      });
    }
    
  
    setPosX((prevPosX) => {
      if (action === "forward" && direction === "left" && prevPosX > 1) return prevPosX - 1;
      if (action === "backward" && direction === "right" && prevPosX > 1) return prevPosX - 1;
      if (action === "forward" && direction === "right" && prevPosX < 6) return prevPosX + 1;
      if (action === "backward" && direction === "left" && prevPosX < 6) return prevPosX + 1;
      return prevPosX;
    });
  
    setPosY((prevPosY) => {
      if (action === "forward" && direction === "up" && prevPosY > 1) return prevPosY - 1;
      if (action === "backward" && direction === "down" && prevPosY > 1) return prevPosY - 1;
      if (action === "forward" && direction === "down" && prevPosY < 4) return prevPosY + 1;
      if (action === "backward" && direction === "up" && prevPosY < 4) return prevPosY + 1;
      return prevPosY;
    });
  };
  
  // Function to render pucks based on board data
  const renderPucks = () => {
    if (!boardData) return null;

    return boardData.board.map((row, rowIndex) => 
      row.map((cell, colIndex) => {
        // Skip rendering if puck has been picked up
        if (pickedPucks.has(`${rowIndex},${colIndex}`)) return null;
        
        if (cell === "G") {
          return (
            <div
              key={`green-${rowIndex}-${colIndex}`}
              className="absolute w-6 h-6 z-10 bg-green-500 rounded-full"
              style={{
                top: `${((rowIndex + 1) / gridRows) * 100}%`,
                left: `${((colIndex + 1) / gridCols) * 100}%`,
                transform: "translate(-43%, -43%)"
              }}
            />
          );
        } else if (cell === "R") {
          return (
            <div
              key={`red-${rowIndex}-${colIndex}`}
              className="absolute w-6 h-6 z-10 bg-red-500 rounded-full"
              style={{
                top: `${((rowIndex + 1) / gridRows) * 100}%`,
                left: `${((colIndex + 1) / gridCols) * 100}%`,
                transform: "translate(-43%, -43%)"
              }}
            />
          );
        }
        return null;
      })
    );
  };

  const stopTimer = () => {
    setIsRunning(false);
    setTimerStarted(false);
    setIsPaused(true);
  };

  return (
    <div className={`flex flex-col items-center justify-center h-screen p-4  z-0 relative overflow-hidden transition-colors duration-200 ease-in-out  ${darkMode ? " bg-[#121212] text-white" : "bg-gray-100 text-gray-900"}`}>
      {/* Dark Mode Toggle */}
      <button onClick={toggleDarkMode} className="absolute top-4 right-4 p-2 rounded-full bg-[#121212] dark:bg-gray-200 text-gray-200 dark:text-gray-900 z-20 shadow-lg transition-transform duration-100 ease-in-out active:scale-95">
        {darkMode ? <Sun size={20} /> : <Moon size={20} />}
      </button>
      
      {/* Command display - only shown when game is running */}
      {/*timerStarted && (
        <div 
          className="absolute top-4 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white px-4 py-2 rounded-full z-20 shadow-lg flex items-center gap-2 font-medium"
        >
          <Boxes size={18} />
          Command: {getCommandName(currentCommand)} ({instructionIndex})
        </div>
      )*/}
      
      {/* Background Dots */}
      <div className="absolute inset-0 z-1 pointer-events-none" style={{
        backgroundImage: darkMode
          ? "radial-gradient(circle, rgba(255,255,255,0.1) 1px, transparent 1px)"
          : "radial-gradient(circle, rgba(0,0,0,0.1) 1px, transparent 1px)",
        backgroundSize: "10px 10px",
        maskImage: "radial-gradient(circle, rgba(0, 0, 0, 1) 30%, rgba(0, 0, 0, 0) 100%)",
        WebkitMaskImage: "radial-gradient(circle, rgba(0, 0, 0, 1) 30%, rgba(0, 0, 0, 0) 100%)"
      }}></div>
      
      {/* Floating Title Card in the Upper Left Corner */}
      <Card className="z-20 absolute top-4 left-4 bg-[#121212] dark:bg-gray-200 text-gray-200 dark:text-gray-900 shadow-xl px-5 py-3 flex items-center gap-3">
          <BringToFront size={28} />
          <h1 className="text-2xl font-bold">Robot Game Dashboard</h1>
      </Card>
    
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-2xl relative z-10">
        <Card className="w-full bg-white dark:bg-neutral-900 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.03)]">
          <CardContent className="flex flex-col items-center p-6">
            <h2 className="text-xl font-semibold">Time Remaining</h2>
            <p className="text-2xl mt-2 drop-shadow-[0px_4px_6px_rgba(0,0,0,0.3)] dark:drop-shadow-[0px_0px_12px_rgba(255,255,255,0.6)]">{Math.floor(timeLeft / 60)}:{(timeLeft % 60).toString().padStart(2, '0')}</p>
            <div className="flex gap-4">
              <Button onClick={startGame} disabled={isRunning} className="mt-4 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)] font-bold transition-transform duration-100 ease-in-out active:scale-95">
                  {timerStarted ? "Resume Game" : "Start Game"}
              </Button>
              <Button 
                onClick={() => {
                  stopTimer();
                  setScore(score + 200 + timeLeft*3);
                }} 
                disabled={!timerStarted || !isRunning} 
                className="mt-4 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)] font-bold transition-transform duration-100 ease-in-out active:scale-95">
                  <TimerOff size="20"/>
              </Button>
            </div>
          </CardContent>
        </Card>
        <Card className="w-full bg-white dark:bg-neutral-900 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.03)]">
          <CardContent className="flex flex-col items-center p-6">
            <h2 className="text-xl font-semibold ">Score</h2>
            <p className="text-2xl mt-2 drop-shadow-[0px_4px_6px_rgba(0,0,0,0.3)] dark:drop-shadow-[0px_0px_12px_rgba(255,255,255,0.6)]">{score}</p>
            <div className="flex gap-4 mt-4">
                <Button onClick={() => setScore(score + 50)} className="shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)] font-bold transition-transform duration-100 ease-in-out active:scale-95">+50</Button>
                <Button onClick={() => setScore(score - 50)} className="shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)] font-bold transition-transform duration-100 ease-in-out active:scale-95">-50</Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Game Grid Card */}
      <Card className="z-10 w-full flex-shrink-0 max-w-2xl mt-6 bg-white dark:bg-neutral-900 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.03)]">
        <CardContent className="px-10 pt-6 pb-10 flex flex-col items-center">
          <h2 className="text-xl font-semibold mb-4">Game Grid</h2>
          <div className="relative w-full h-96 rounded-lg border-4 border-gray-900 dark:border-gray-200 shadow-xl dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)]">
            {/* Star in top-left */}
            <div className="relative w-16 h-16 z-10 text-yellow-500" style={{ top: "15%", left: "11%" }}>
              <Star size={42} fill="currentColor" />
            </div>
            
            {/* Render pucks from board data */}
            {renderPucks()}

            {/* Vertical Lines */}
            {[...Array(6)].map((_, i) => (
              <div key={`v-${i}`} className="absolute top-0 bottom-0 w-[4px] bg-gray-900 dark:bg-gray-200" style={{ left: `${((i + 1) / 7) * 100}%` }}></div>
            ))}
            {/* Horizontal Lines */}
            {[...Array(4)].map((_, i) => (
              <div key={`h-${i}`} className="absolute left-0 right-0 h-[4px] bg-gray-900 dark:bg-gray-200" style={{ top: `${((i + 1) / 5) * 100}%` }}></div>
            ))}

            {/* Robot */}
            <div className="absolute w-16 h-16 z-10 text-gray-600 " style={robotStyle}>
            <CircleArrowUp size={64} className="drop-shadow-[0px_0px_2px_rgba(255,255,255,1)] dark:drop-shadow-[0px_0px_2px_rgba(0,0,0,1)] text-primary"/>
            </div>

          </div>
        </CardContent>
      </Card>

          
      {/* Arm switch & Emergency Stop Button */}
      <div className="mt-6 flex gap-4">
        <Button 
            onClick={() => setIsArmed((prev) => !prev)} 
            className="z-10 bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded shadow-[0px_4px_12px_rgba(0,0,255,0.4)] transition-transform duration-100 ease-in-out active:scale-95">
            <ShieldCheck size={20} />
        </Button>
        <Button 
            onClick={stopRobot} 
            disabled={!isArmed}
            className="z-10 bg-red-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded shadow-[0px_4px_12px_rgba(255,0,0,0.4)] transition-transform duration-100 ease-in-out active:scale-95">
            Emergency Stop
        </Button>
        <Button
            onClick={() => {sendCommand("manualcontrol"); setManualControl((prev) => !prev);}}
            className={`z-10 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)] font-bold transition-transform duration-100 ease-in-out active:scale-95
                ${manualControl ? "opacity-100" : ""}`} >
            <Joystick size={20} className={manualControl ? "text-red-600" : ""}/>
            Manual Control
        </Button>
        <Button
            onClick={() => {sendCommand("kalibratie");}}
            disabled={isRunning}
            className="z-10 bg-green-700 hover:bg-green-800 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)] font-bold transition-transform duration-100 ease-in-out active:scale-95">
            <RefreshCw size={20}/>
            Calibration
        </Button>
        <Button
            onClick={() => {
                sendCommand("resetroute");
                setDirection("right");
                setRotationAngle(90);
                setPosX(1);
                setPosY(1);
            }}
            className="z-10 bg-cyan-700 hover:bg-cyan-800 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)] font-bold transition-transform duration-100 ease-in-out active:scale-95">
            <Route size={20}/>
            Reset
        </Button>
      </div>
      <div className="absolute left-0 top-1/2 transform -translate-y-1/2 p-4">
        <BlockProgressBar pickedPucks={pickedPucks} />
      </div>
      
      {/* Manual Control Section */}
      <div className={`flex items-center h-screen fixed right-32 p-4 w-128 transition-opacity duration-100 ${manualControl ? 'opacity-100' : 'opacity-0'}`}>
        <Card className="bg-white dark:bg-neutral-900 shadow-xl dark:shadow-[0px_4px_12px_rgba(255,255,255,0.03)] w-128 h-128 flex items-center justify-center p-4">
        <div className="grid grid-cols-3 grid-rows-3 gap-2 w-full h-full">
          {/* Top Left */}
          <div />
          {/* Top Center - Up Button */}
          <div>
            <Button onClick={() => sendCommand("forward")} className="w-full h-full flex items-center justify-center p-4 transition-transform duration-100 ease-in-out active:scale-95 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)]">
              <ArrowUp size={24}/>
            </Button>
          </div>
          {/* Top Right */}
          <div />
          {/* Middle Left - Left Button */}
          <div>
            <Button onClick={() => sendCommand("left")} className="w-full h-full flex items-center justify-center p-4 transition-transform duration-100 ease-in-out active:scale-95 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)]">
              <RotateCcw size={24}/>
            </Button>
          </div>
          {/* Center - Empty */}
          <div>
            <Button onClick={() => sendCommand("pickup")} className="w-full h-full flex items-center justify-center p-4 bg-blue-500 hover:bg-blue-600 transition-transform duration-100 ease-in-out active:scale-95 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)]">
              <Hand size={24}/>
            </Button>
          </div>
          {/* Middle Right - Right Button */}
          <div>
            <Button onClick={() => sendCommand("right")} className="w-full h-full flex items-center justify-center p-4 transition-transform duration-100 ease-in-out active:scale-95 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)]">
              <RotateCw size={32}/>
            </Button>
          </div>
          {/* Bottom Left */}
          <div />
          {/* Bottom Center - Down Button */}
          <div>
            <Button onClick={() => sendCommand("backward")} className="w-full h-full flex items-center justify-center p-4 transition-transform duration-100 ease-in-out active:scale-95 shadow-lg dark:shadow-[0px_4px_12px_rgba(255,255,255,0.1)]">
              <ArrowDown size={32}/>
            </Button>
          </div>
          {/* Bottom Right */}
          <div />
        </div>
        </Card>
      </div>

      <p className="absolute bottom-3 right-4 text-sm text-gray-600 dark:text-gray-300">
        © {new Date().getFullYear()} Team 209 P&O 1b
      </p>
      
      {/*
      <Card className="absolute bottom-4 left-4 px-3 pt-2 text-sm w-60 bg-[#121212] dark:bg-gray-200 text-gray-200 dark:text-gray-900 shadow-lg">
        <p className="font-bold">PICO CONNECTION STATUS: {isConnected === false ? "⚠️" : "✅"} </p>
        <Separator className="mt-1 mb-0 bg-muted-foreground max-w-[100%]" />
        <Accordion type="single" collapsible className="w-full -mt-3 -mb-1" >
          <AccordionItem value="item-1" className="border-b-0">
            <AccordionTrigger><h3 className="text-md font-semibold text-secondary -mb-2">Console Logs:</h3></AccordionTrigger>
            <AccordionContent className="">
              <LogViewer logs={logs} maxMessages={4}/>
            </AccordionContent>
          </AccordionItem>
        </Accordion> 
      </Card>
      */}

      <Card className="absolute bottom-4 left-4 px-3 text-sm w-72 bg-white dark:bg-neutral-900 shadow-xl dark:shadow-[0px_4px_12px_rgba(255,255,255,0.03)]">
        <Accordion type="single" collapsible className="w-full" >
          <AccordionItem value="item-1" className="border-b-0">
            <AccordionTrigger><p className="font-bold">PICO CONNECTION STATUS: {isConnected === false ? "⚠️" : "✅"} </p></AccordionTrigger>
            <AccordionContent className="">
              <LogViewer logs={logs} maxMessages={4}/>
            </AccordionContent>
          </AccordionItem>
        </Accordion> 
      </Card>

    </div>
  );
}
