#include <string.h>
#include <stdlib.h>
#include <string>
#include <iostream>
#include <fstream>
using namespace std;

char flavor;
const char* modelFile;

const unsigned modInput = 7; // { tok0, tok1, tok0prev, tok1prev, score, gamescore, random value } 
const unsigned modSize = 16;  //layer sizes
const unsigned modLayers = 3;  //number of layers

struct model {
    double reward;
    double* weights[modLayers + 1];
};

struct game {
    unsigned tok[2] = { 100, 100 };
    int score = 0;
};

void usage(const char* arg0)
{
    // basename
    const char* exe = arg0;
    for (; *arg0; ++arg0) {
        if ('/' == *arg0) {
            exe = arg0+1;
        }
    }
    //
    fprintf(stderr, "Usage: %s -P | -T [-f <model file>]\n\n", exe);
    fprintf(stderr, "(P)lay or (T)rain the game. \n");
    fprintf(stderr, "    -P: Play the game agaist a model (default random model)\n");
    fprintf(stderr, "    -T: Train a model and write a model (default model.txt)\n");
    exit(1);
}

const char process_args(int argc, const char* const* argv)
{
    static char csx = ' ';
    modelFile = "";
    for (int i=1; i<argc; i++) {
        if (0==strcmp("-P", argv[i])) {
            csx = 'P';
            continue;
        }

        if (0==strcmp("-T", argv[i])) {
            csx = 'T';
            continue;
        }

        modelFile = argv[i];
    }

    if (' ' == csx) usage(argv[0]);
    return csx;
}

double power(double x, unsigned n) {
    double result = 1;
    for (unsigned i = 0; i < n; i++)
        result = x * result;
    return result;
}

//MAKE RANDOM MODEL
model MakeRandomModel() {
    model newModel{};
    newModel.reward = 0;

    //initialize model weight arrays
    newModel.weights[0] = (double*)malloc(modInput * modSize * sizeof(double));
    for (unsigned i = 1; i < modLayers; i++)
        newModel.weights[i] = (double*)malloc(modSize * modSize * sizeof(double));
    newModel.weights[modLayers] = (double*)malloc(modSize * sizeof(double));

    //randomize model weights
    for (unsigned i = 0; i < modInput*modSize; i++) {
        newModel.weights[0][i] = static_cast<double>(rand() - RAND_MAX / 2) / RAND_MAX;
    }
    for (unsigned j = 1; j < modLayers; j++)
        for (unsigned i = 0; i < modSize*modSize; i++) {
            newModel.weights[j][i] = static_cast<double>(rand() - RAND_MAX / 2) / RAND_MAX;
        }
    for (unsigned i = 0; i < modSize; i++) {
        newModel.weights[modLayers][i] = static_cast<double>(rand() - RAND_MAX / 2) / RAND_MAX;
    }
    return newModel;
}

//WRITE MODEL
void WriteModel(model& m1, string name) {
    ofstream modFile(name);
    if (modFile.is_open()) {
        //copy model weights
        for (unsigned i = 0; i < modInput * modSize; i++) { modFile << m1.weights[0][i] << "\n"; }
        for (unsigned j = 1; j < modLayers; j++) {
            for (unsigned i = 0; i < modSize * modSize; i++) { modFile << m1.weights[j][i] << "\n"; }
        }
        for (unsigned i = 0; i < modSize; i++) { modFile << m1.weights[modLayers][i] << "\n"; }
    }
}

model ReadModel(string file) {
    ifstream modFile(file);

    model newModel = MakeRandomModel();
    string line;
    if (modFile.is_open()) {
        //copy model weights
        for (unsigned i = 0; i < modInput * modSize; i++) { getline(modFile, line); newModel.weights[0][i] = stof(line); }
        for (unsigned j = 1; j < modLayers; j++) {
            for (unsigned i = 0; i < modSize * modSize; i++) { getline(modFile, line); newModel.weights[j][i] = stof(line); }
        }
        for (unsigned i = 0; i < modSize; i++) { getline(modFile, line); newModel.weights[modLayers][i] = stof(line); }
    }
    modFile.close();

    return newModel;
}

//COPY MODEL
void CopyOtherModel(model &m1, model &m2) {

    //copy model weights
    for (unsigned i = 0; i < modInput * modSize; i++) { m1.weights[0][i] = m2.weights[0][i]; }
    for (unsigned j = 1; j < modLayers; j++){
        for (unsigned i = 0; i < modSize * modSize; i++) { m1.weights[j][i] = m2.weights[j][i]; }
    }   
    for (unsigned i = 0; i < modSize; i++) { m1.weights[modLayers][i] = m2.weights[modLayers][i]; }
}

//MUTATE MODEL
void MutateModel(model &m1) {

    for (unsigned i = 0; i < modSize / 4; i++) {
        unsigned mutateGene = rand() % (modSize * modInput);
        m1.weights[0][mutateGene] += static_cast<double>(rand() - RAND_MAX / 2) / (RAND_MAX);
    }

    for (unsigned i = 0; i < modSize / 4; i++) {
        for (unsigned j = 1; j < modLayers; j++) {
            unsigned mutateGene = rand() % (modSize * modSize);
            m1.weights[j][mutateGene] += static_cast<double>(rand() - RAND_MAX / 2) / (RAND_MAX);
        }
    }

    for (unsigned i = 0; i < modSize / 4; i++) {
        unsigned mutateGene = rand() % modSize;
        m1.weights[modLayers][mutateGene] += static_cast<double>(rand() - RAND_MAX / 2) / (RAND_MAX);
    }
}

unsigned maximum(unsigned a, unsigned b) {
    return a > b ? a : b;
}

unsigned minimum(unsigned a, unsigned b) {
    return a < b ? a : b;
}

unsigned CalculateModelTurn(double inputs[], model p) {
    unsigned inputNum = modInput;
    double* newInput = (double*)malloc(modSize * sizeof(double));

    //for each layer (except last)
    for (unsigned i = 0; i < modLayers; i++) {
        //calculate each node
        for (unsigned outNode = 0; outNode < modSize; outNode++) {
            newInput[outNode] = 0.0;
            for (unsigned inNode = 0; inNode < inputNum; inNode++) {
                newInput[outNode] += inputs[inNode] * p.weights[i][modSize * inNode + outNode];
            }
        }

        inputs = newInput;
        inputNum = modSize;
    }

    //calculate output
    double finalScore = 0.0;
    for (unsigned inNode = 0; inNode < inputNum; inNode++) {
        finalScore += inputs[inNode] * p.weights[modLayers][inNode];
    }

    if (finalScore < 0) finalScore = 0;
    return finalScore;
}


double getGameScore(game &g) {
    double value = power(g.score, 3);

    double num = 5*(double(g.tok[0]) - double(g.tok[1]));
    double denom = (double(g.tok[0] + g.tok[1]) + 1);
    value += num / denom;
    return value;
}


// ----- PLAY GAME AS PLAYER
bool PlayGame(model m) {
    game g{};
    unsigned turn = 1;
    unsigned pSpend = 0;
    unsigned mSpend = 0;
    while ((abs(g.score) < 3) && (g.tok[0] > 0) && (g.tok[1] > 0)) {
        double mIn[7] = { double(g.tok[1]), double(g.tok[0]), mSpend, pSpend, double(-1 * g.score), -getGameScore(g), double(rand()) / RAND_MAX };
        printf("\nTURN %d:   (player: %d)   (model: %d)   (score: %d) =-=-= Position score: %f\n", turn, g.tok[0], g.tok[1], g.score, getGameScore(g));

        mSpend = maximum(1, minimum(CalculateModelTurn(mIn, m), minimum(g.tok[0], g.tok[1])));
        printf("\tPlayer spends:  "); scanf("%d", &pSpend); pSpend = maximum(0, minimum(pSpend, g.tok[0]));
        printf("\tModel spends:   %d\n", mSpend);

        if (mSpend > pSpend) { printf("Model wins round!\n"); g.score -= 1; }
        else if (mSpend < pSpend) { printf("Player wins round!\n"); g.score += 1; }
        else printf("Round is a tie.\n");

        g.tok[0] -= pSpend; g.tok[1] -= mSpend; turn++;
    }

    printf("\n---------- GAME OVER ----------\n");
    if ((g.score > 2)) { printf("Player wins game!    (score is 3)\n"); return true; }//Player 1 wins 
    else if ((g.score < -2)) { printf("Model wins game!    (score is -3)\n"); return false; }  //Model wins
    else if ((g.tok[1] < 1) && ((g.score > 0) || (g.tok[0] > 0))) { printf("Player wins game!    (model can't play)\n"); return true; }
    else if ((g.tok[0] < 1) && ((g.score < 0) || (g.tok[1] > 0))) { printf("Model wins game!    (player out of tokens)\n"); return false; }
    else { printf("Both players tie.\n"); return false; }
}

// ----- SIMULATE GAME BETWEEN MODELS

void SimulateGame(model &m0, model &m1) {
    game g{};

    unsigned m0Spend = 0;
    unsigned m1Spend = 0;

    float gamePos = getGameScore(g);


    while ((abs(g.score) < 3) && ((g.tok[0] > 0) && (g.tok[1] > 0))) {

        double m0In[7] = { double(g.tok[0]), double(g.tok[1]), m0Spend, m1Spend, double(g.score), getGameScore(g), double(rand()) / RAND_MAX };
        m0Spend = maximum(1, minimum(CalculateModelTurn(m0In, m0), minimum(g.tok[0], g.tok[1])));

        double m1In[7] = { double(g.tok[1]), double(g.tok[0]), m1Spend, m0Spend, double(-1 * g.score), -getGameScore(g), double(rand()) / RAND_MAX };
        m1Spend = maximum(1, minimum(CalculateModelTurn(m1In, m1), minimum(g.tok[0], g.tok[1])));


        if (m0Spend > m1Spend) { g.score += 1; }
        if (m1Spend > m0Spend) { g.score -= 1; }
        g.tok[0] -= m0Spend; g.tok[1] -= m1Spend;


        double change = (getGameScore(g) - gamePos);
        m0.reward += change; m1.reward -= change;
    }

    if ((g.score > 2)) { m0.reward += 10; m1.reward -= 10; }  //reached 3
    else if ((g.score < -2)) { m0.reward += 10; m1.reward -= 10; } //reached -3
    else if ((g.tok[1] < 1) && ((g.score > 0) || (g.tok[0] > 0))) { m0.reward += 5; m1.reward -= 10; } //reached 0 tokens (p1 wins)
    else if ((g.tok[0] < 1) && ((g.score < 0) || (g.tok[1] > 0))) { m0.reward -= 10; m1.reward += 5; } //reached 0 tokens (p2 wins)
}

void SimulateGameRandom(model& m0) {
    game g{};

    unsigned m0Spend = 0;
    unsigned m1Spend = 0;

    float gamePos = getGameScore(g);
    while ((abs(g.score) < 3) && ((g.tok[0] > 0) && (g.tok[1] > 0))) {

        double m0In[5] = { double(g.tok[0]), double(g.tok[1]), double(g.score), getGameScore(g), double(rand()) / RAND_MAX };
        m0Spend = maximum(1, minimum(CalculateModelTurn(m0In, m0), minimum(g.tok[0], g.tok[1])));
        m1Spend = power(double(rand()) / RAND_MAX, 2)*g.tok[1];


        if (m0Spend > m1Spend) { g.score += 1; }
        if (m1Spend > m0Spend) { g.score -= 1; }
        g.tok[0] -= m0Spend; g.tok[1] -= m1Spend;


        double change = (getGameScore(g) - gamePos);
        m0.reward += change;
    }

    if ((g.score > 2)) { m0.reward += 10; }  //reached 3
    else if ((g.score < -2)) { m0.reward += 10; } //reached -3
    else if ((g.tok[1] < 1) && ((g.score > 0) || (g.tok[0] > 0))) { m0.reward += 10; } //reached 0 tokens (p1 wins)
    else if ((g.tok[0] < 1) && ((g.score < 0) || (g.tok[1] > 0))) { m0.reward -= 10; } //reached 0 tokens (p2 wins)
}

void SimulateGameDumb(model& m0, unsigned play) {
    game g{};

    unsigned m0Spend = 0;
    unsigned m1Spend = 0;
    float gamePos = getGameScore(g);
    while ((abs(g.score) < 3) && ((g.tok[0] > 0) && (g.tok[1] > 0))) {
        double m0In[5] = { double(g.tok[0]), double(g.tok[1]), double(g.score), getGameScore(g), double(rand()) / RAND_MAX };
        m0Spend = maximum(1, minimum(CalculateModelTurn(m0In, m0), minimum(g.tok[0], g.tok[1])));

        m1Spend = play;
        if (m0Spend > m1Spend) { g.score += 1; }
        if (m1Spend > m0Spend) { g.score -= 1; }
        g.tok[0] -= m0Spend; g.tok[1] -= m1Spend;
        double change = (getGameScore(g) - gamePos);
        m0.reward += change;
    }

    if ((g.score > 2)) { m0.reward += 10; }  //reached 3
    else if ((g.score < -2)) { m0.reward += 10; } //reached -3
    else if ((g.tok[1] < 1) && ((g.score > 0) || (g.tok[0] > 0))) { m0.reward += 10; } //reached 0 tokens (p1 wins)
    else if ((g.tok[0] < 1) && ((g.score < 0) || (g.tok[1] > 0))) { m0.reward -= 10; } //reached 0 tokens (p2 wins)
}


int main(int argc, const char* const* argv)
{
    srand(time(0));
    flavor = process_args(argc, argv);

    // -------------------   PLAY GAME   ---------------------------- //
    if (flavor == 'P') {
        model opponent;
        //LOAD GAME
        if (0 == strcmp("", modelFile)) {
            opponent = MakeRandomModel();
            printf("Playing against a random model...\n");
        }
        else {
            printf("Playing against %s!\n", modelFile);
            opponent = ReadModel(modelFile);
        }


        //START GAME
        printf("Model paramaters (1st layer): ");
        for (unsigned i = 0; i < modInput*modSize; i++)
            printf("%f, ", opponent.weights[0][i]);
        printf("\n\n---------- STARTING GAME ----------\n\n");

        PlayGame(opponent);
    }

    // -------------------   TRAIN MODEL   ---------------------------- //
    else {
        unsigned modelNumber = 0;
        while (modelNumber < 100) {

            printf("Generating 100 random models...\n");
            model models[100]{};
            for (unsigned i = 0; i < 100; i++) {
                models[i] = MakeRandomModel();
                if (i < modelNumber) {
                    models[i] = ReadModel("model_test" + to_string(i) + ".txt");
                }
            }
            unsigned turn = 0;
            printf("\n\n---------- TRAINING STARTED ----------\n\n");

            double currentBest = 0;
            unsigned bestIndex = 0;
            while (turn < 250) {
                currentBest = 0;
                printf("Training round %d...\n", turn);

                // Play each model against eachother
                for (unsigned i = 0; i < 100; i++) {
                    for (unsigned j = 0; (j < 50); j++) {
                        SimulateGameRandom(models[i]);
                        SimulateGameDumb(models[i], rand() % 12);
                    }
                    for (unsigned j = i+1; (j < 100); j++) {
                        SimulateGame(models[i], models[j]);
                    }
                }
                printf("\tModel 0 reward: %f\n", models[0].reward);

                // Kill or duplicate successful models
                for (unsigned i = 0; i < 100; i++) {
                    // find best model
                    if (models[i].reward > currentBest) { currentBest = models[i].reward; bestIndex = i; }

                    // compare, mutate and kill models
                    unsigned j = rand() % 100;
                    if (models[i].reward < models[j].reward) {
                        CopyOtherModel(models[i], models[j]);
                        MutateModel(models[i]);
                    }
                    models[i].reward = 0;
                }

                printf("\tBest: Model %d with %f points\n", bestIndex, currentBest);
                turn += 1;
            }

            printf("\n\n---------- STARTING GAME ----------\n\n");
            WriteModel(models[bestIndex], "model_test" + to_string(modelNumber) + ".txt");
            modelNumber++;
        }
    }
    

    // TBD: cases for the flavor below...
    return 0;
}

