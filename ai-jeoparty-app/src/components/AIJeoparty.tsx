import React, { useState, useRef } from 'react';

const AIJeoparty = () => {
  // Game state
  const [gameState, setGameState] = useState({
    currentQuestion: null,
    answeredQuestions: {},
    scores: {
      team1: 0,
      team2: 0
    },
    currentTeam: 'team1', // Tracks which team is answering
    showAnswer: false,
    audioPlaying: false
  });
  
  const audioRef = useRef(null);
  
  // Categories and questions
  const categories = [
    { 
      name: "Lost in translation", 
      type: "audio",
      questions: [
        { points: 100, audio: "./public/assets/ai_songs/Boing.mp3", question: "Hvad er navnet på sangen originalt?", answer: "Boing" },
        { points: 200, audio: "./public/assets/ai_songs/Vi Maler Byen Rød.mp3", question: "Hvad er navnet på sangen originalt?", answer: "Vi maler byen rød" },
        { points: 300, audio: "./public/assets/ai_songs/Nu kommer fuglene tilbage (DK - ENG - DE - DA).mp3", question: "Hvad er navnet på sangen originalt?", answer: "Lyse nætter" },
        { points: 400, audio: "./public/assets/ai_songs/True Colours (Trolls shoutout).mp3", question: "Hvad er navnet på sangen originalt?", answer: "True Colours" },
        { points: 500, audio: "./public/assets/ai_songs/where.mp3", question: "Hvad er navnet på sangen originalt?", answer: "Where Is the Love (Where Is the Love?)" }
      ]
    },
    { 
      name: "DJ, give it a spin", 
      type: "audio",
      questions: [
        { points: 100, audio: "./public/assets/ai_songs/Ibiza.mp3", question: "Hvad er navnet på sangen originalt?", answer: "Benny Jamz, Gilli, og Kesi + Ibiza" },
        { points: 200, audio: "./public/assets/ai_songs/Feberdrømmer Xx Dubai.mp3", question: "Hvad er navnet på sangen originalt?", answer: "Tobias Rahim + Feberdrømmer Xx Dubai" },
        { points: 300, audio: "./public/assets/ai_songs/Fucking Nummer.mp3", question: "Hvad er navnet på sangen originalt?", answer: "Ukendt Kunstner + Fucking Nummer" },
        { points: 400, audio: "./public/assets/ai_songs/Mest ondt.mp3", question: "Hvad er navnet på sangen originalt?", answer: "Burhan G. og Medina + Mest Ondt" },
        { points: 500, audio: "./public/assets/ai_songs/SutDen.mp3", question: "Hvad er navnet på sangen originalt?", answer: "UAK + Suger coke fra dit røvhul" }
      ]
    },
    { 
      name: "Hva' ska' æ' kost?", 
      type: "image",
      questions: [
        { points: 100, image: "./public/assets/dba/Rugeæg/image.png", question: "Få muligheden for at udklække dine egne kobber maran kyllinger fra en flok af blå kobber maran hane og sort kobber maran høner, kendt for deres smukke, mørkebrune æg. Disse rolige og søde høns er en fantastisk tilføjelse til enhver have.", answer: "15 kr." },
        { points: 200, image: "./public/assets/dba/Commodore/image.png", question: "Oplev ægte nostalgi med denne smukke Commodore PC-1, komplet med original emballage og fuldt fungerende tilbehør. Perfekt til samlere og retro-entusiaster, der ønsker at eje et stykke computergeschichte.", answer: "5.500 kr." },
        { points: 300, image: "./public/assets/dba/Pillefyr/image.png", question: "Opgrader din opvarmning med dette velfungerende BioMax 16 pillefyr, der nu søger et nyt hjem efter udskiftning til varmepumpe. Inkluderet er en tilhørende pillesilo, der sikrer en nem og effektiv opvarmningsløsning.", answer: "2.000 kr." },
        { points: 400, image: "./public/assets/dba/Prisme lysekrone fra K&Co - Antik prisme lysekronekrone købt hos K&Co på Frederiksberg.  Ca 70 cm høj og 65 cm bred. Købspris kr 22.000 - Pris på DBA 11.000.png", question: "Tilføj et strejf af elegance til dit hjem med denne antikke prisme lysekrone fra K&Co, købt på Frederiksberg. Med sine imponerende dimensioner vil denne lysekrone skabe en luksuriøs atmosfære i ethvert rum.", answer: "11.000 kr." },
        { points: 500, image: "./public/assets/dba/Jesus på korset, Træ/Jesus på korset, træ og gips, 400 år gl..png", question: "Besid et unikt stykke dansk kirkehistorie med dette 400 år gamle krucifiks, håndlavet af træ og gips. Denne imponerende Jesusfigur, der stammer fra en nedlagt kirke, udstråler en tidløs skønhed og åndelig dybde.", answer: "800.000 kr." }
      ]
    },
    { 
      name: "AI Landmarks", 
      type: "image",
      questions: [
        { points: 100, image: "./public/assets/ai_images/image.png", question: "Hvilket historisk landmærke er dette?", answer: "Den Gamle By" },
        { points: 200, image: "./public/assets/ai_images/randers.png", question: "Hvilket sted i Danmark er på billedet?", answer: "Randers Regnskov" },
        { points: 300, image: "./public/assets/ai_images/mont.png", question: "Hvilket historisk landmærke er dette?", answer: "Mont Saint-Michel" },
        { points: 400, image: "./public/assets/ai_images/troll.png", question: "Hvilket historisk landmærke er dette?", answer: "Trolltunga" },
        { points: 500, image: "./public/assets/ai_images/panama.png", question: "Hvilket historisk landmærke er dette?", answer: "Panamakanalen" }
      ]
    },
    { 
      name: "AI Movie Scenes", 
      type: "image",
      questions: [
        { points: 100, image: "./public/assets/ai_images/druk.png", question: "Hvilken film er dette fra?", answer: "Druk" },
        { points: 200, image: "./public/assets/ai_images/inception.png", question: "Hvilken film er dette fra?", answer: "Inception" },
        { points: 300, image: "./public/assets/ai_images/lion.png", question: "Hvilken film er dette fra?", answer: "Løvernes Konge" },
        { points: 400, image: "./public/assets/ai_images/øl.png", question: "Hvilken film er dette fra?", answer: "Min søsters børn" },
        { points: 500, image: "./public/assets/ai_images/urørlige.png", question: "Hvilken film er dette fra?", answer: "De Urørlige" }
      ]
    }
  ];

  // Functions to handle game interactions
  const handleTileClick = (categoryIndex, questionIndex) => {
    const category = categories[categoryIndex];
    const question = category.questions[questionIndex];
    const questionId = `${categoryIndex}-${questionIndex}`;
    
    // Check if already answered
    if (gameState.answeredQuestions[questionId]) return;
    
    setGameState({
      ...gameState,
      currentQuestion: {
        categoryIndex,
        questionIndex,
        ...question,
        categoryName: category.name,
        type: category.type,
        id: questionId
      },
      showAnswer: false,
      audioPlaying: false
    });
  };

  const closeQuestion = () => {
    setGameState({
      ...gameState,
      currentQuestion: null,
      audioPlaying: false
    });
    
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  };

  const toggleAnswer = () => {
    setGameState({
      ...gameState,
      showAnswer: !gameState.showAnswer
    });
  };

  const handleScoreUpdate = (correct, team) => {
    const points = gameState.currentQuestion.points;
    const questionId = gameState.currentQuestion.id;
    
    setGameState({
      ...gameState,
      scores: {
        ...gameState.scores,
        [team]: gameState.scores[team] + (correct ? points : -points)
      },
      answeredQuestions: {
        ...gameState.answeredQuestions,
        [questionId]: true
      },
      currentQuestion: null,
      audioPlaying: false,
      currentTeam: team === 'team1' ? 'team2' : 'team1' // Toggle team for next turn
    });
    
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
  };

  const switchTeam = () => {
    setGameState({
      ...gameState,
      currentTeam: gameState.currentTeam === 'team1' ? 'team2' : 'team1'
    });
  };

  const playAudio = () => {
    if (audioRef.current) {
      if (gameState.audioPlaying) {
        audioRef.current.pause();
        setGameState({ ...gameState, audioPlaying: false });
      } else {
        audioRef.current.play();
        setGameState({ ...gameState, audioPlaying: true });
      }
    }
  };

  // Render functions
  const renderGameBoard = () => (
    <div className="grid grid-cols-5 gap-4 w-full">
      {/* Category Headers */}
      {categories.map((category, categoryIndex) => (
        <div 
          key={`category-${categoryIndex}`}
          className="bg-blue-800 text-white font-bold p-4 rounded-lg text-center"
        >
          {category.name}
        </div>
      ))}
      
      {/* Question Tiles - rendered by point value rows */}
      {[100, 200, 300, 400, 500].map((points, rowIndex) => (
        <React.Fragment key={`row-${points}`}>
          {categories.map((category, categoryIndex) => {
            const questionIndex = rowIndex;
            const questionId = `${categoryIndex}-${questionIndex}`;
            const isAnswered = gameState.answeredQuestions[questionId];
            
            return (
              <div 
                key={`tile-${categoryIndex}-${questionIndex}`}
                onClick={() => handleTileClick(categoryIndex, questionIndex)}
                className={`${
                  isAnswered ? 'bg-gray-700 cursor-default opacity-50' : 'bg-blue-600 hover:bg-blue-700 cursor-pointer'
                } text-yellow-300 font-bold text-3xl p-6 rounded-lg text-center transition-all transform hover:scale-105 flex items-center justify-center`}
              >
                {isAnswered ? "" : `$${points}`}
              </div>
            );
          })}
        </React.Fragment>
      ))}
    </div>
  );

  const renderCurrentQuestion = () => {
    if (!gameState.currentQuestion) return null;
    
    const { categoryName, question, answer, type, audio, image } = gameState.currentQuestion;
    
    return (
      <div className="fixed inset-0 bg-black bg-opacity-80 flex items-center justify-center p-4 z-10">
        <div className="bg-blue-900 text-white rounded-xl p-6 max-w-2xl w-full max-h-full overflow-auto flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-yellow-300 text-2xl font-bold">{categoryName} - ${gameState.currentQuestion.points}</h2>
            <button 
              onClick={closeQuestion}
              className="bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded-full transition-colors"
            >
              ✕
            </button>
          </div>
          
          <div className="flex-grow flex flex-col items-center justify-center gap-4 my-4">
            {type === 'audio' && (
              <div className="flex flex-col items-center gap-2 w-full">
                <button 
                  onClick={playAudio} 
                  className="bg-yellow-500 hover:bg-yellow-600 text-blue-900 px-6 py-3 rounded-lg font-bold text-xl transition-colors"
                >
                  {gameState.audioPlaying ? 'Pause Audio' : 'Play Audio'}
                </button>
                <audio ref={audioRef} src={audio} className="hidden" />
              </div>
            )}
            
            {type === 'image' && (
              <div className="w-full max-h-64 flex justify-center mb-4">
                <img 
                  src={image || "/api/placeholder/400/300"} 
                  alt="Question visual" 
                  className="max-h-full object-contain rounded-lg border-2 border-yellow-300" 
                />
              </div>
            )}
            
            <div className="text-center text-xl font-medium w-full">{question}</div>
            
            {gameState.showAnswer && (
              <div className="mt-4 p-4 bg-yellow-300 text-blue-900 rounded-lg text-xl font-bold text-center w-full">
                {answer}
              </div>
            )}
          </div>
          
          <div className="flex justify-between gap-4 mt-4">
            <button 
              onClick={toggleAnswer}
              className="bg-blue-600 hover:bg-blue-700 flex-1 text-white px-4 py-2 rounded-lg transition-colors"
            >
              {gameState.showAnswer ? 'Hide Answer' : 'Show Answer'}
            </button>
            
            {gameState.showAnswer && (
              <div className="flex gap-2 flex-1">
                <button 
                  onClick={() => handleScoreUpdate(true, gameState.currentTeam)}
                  className="bg-green-600 hover:bg-green-700 flex-1 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Correct
                </button>
                <button 
                  onClick={() => handleScoreUpdate(false, gameState.currentTeam)}
                  className="bg-red-600 hover:bg-red-700 flex-1 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Incorrect
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col items-center gap-6 w-full p-4">
      <div className="flex justify-between items-center w-full">
        <h1 className="text-4xl font-bold text-blue-800">AI Jeopardy</h1>
        <div className="bg-blue-800 text-yellow-300 px-6 py-3 rounded-lg text-2xl font-bold">
          Team 1 Score: ${gameState.scores.team1}
        </div>
        <div className="bg-blue-800 text-yellow-300 px-6 py-3 rounded-lg text-2xl font-bold">
          Team 2 Score: ${gameState.scores.team2}
        </div>
        <div className="bg-blue-800 text-yellow-300 px-6 py-3 rounded-lg text-2xl font-bold">
          Current Team: {gameState.currentTeam === 'team1' ? 'Team 1' : 'Team 2'}
        </div>
      </div>
      
      {renderGameBoard()}
      {renderCurrentQuestion()}
      
      <div className="mt-6 p-4 bg-gray-100 rounded-lg w-full max-w-3xl">
        <h2 className="text-xl font-bold text-blue-800 mb-2">How to Use:</h2>
        <ol className="list-decimal pl-6">
          <li className="mb-2">Replace all "path/to/..." placeholders with actual file paths on your computer</li>
          <li className="mb-2">Customize questions, categories, and answers as needed</li>
          <li className="mb-2">Click on a dollar value to reveal the question</li>
          <li className="mb-2">For audio questions, click "Play Audio" to hear the AI-generated song</li>
          <li className="mb-2">Click "Show Answer" to reveal the correct response</li>
          <li>Score points by selecting "Correct" or "Incorrect" after revealing the answer</li>
        </ol>
      </div>
    </div>
  );
};

export default AIJeoparty;