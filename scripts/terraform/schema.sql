CREATE TABLE Tasks (
    TaskId VARCHAR(255) PRIMARY KEY,
    Question TEXT NOT NULL,
    ExpectedAnswer TEXT,
    Level INT,
    FileName VARCHAR(255),
    FilePath VARCHAR(255),
    Annotations JSONB
);

CREATE TABLE LLMs (
    LLMId SERIAL PRIMARY KEY,
    LLMName VARCHAR(255) NOT NULL,
    Version VARCHAR(50),
    Parameters TEXT
);

CREATE TABLE LLMResponses (
    ResponseId SERIAL PRIMARY KEY,
    TaskId VARCHAR(255) REFERENCES Tasks(TaskId),
    LLMId INT REFERENCES LLMs(LLMId),
    ResponseText TEXT NOT NULL,
    IsAnnotated BOOLEAN DEFAULT FALSE,
    ResultCategory VARCHAR(50),
    Timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);