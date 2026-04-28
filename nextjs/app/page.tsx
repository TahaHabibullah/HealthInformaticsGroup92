'use client';

import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import {
  Typography,
  Box,
  TextField,
  IconButton,
  Paper,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Backdrop,
  ThemeProvider,
  createTheme,
  Container
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';

const theme = createTheme({
  palette: {
    mode: 'dark',
    background: {
      default: '#1d1d1d',
      paper: '#202020',
    },
    primary: {
      main: '#004D98',
    },
    secondary: {
      main: '#A50044',
    },
  },
  typography: {
		fontFamily: "Open Sans",
		fontSize: 13,
		fontWeightRegular: 600
	},
});

export default function Home() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [openDialog, setOpenDialog] = useState(false);
  const [patientName, setPatientName] = useState('');
  const [birthDate, setBirthDate] = useState('');
  const [encounterId, setEncounterId] = useState('');
  const [isSaved, setIsSaved] = useState(false);

  const handleSubmit = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setLoading(true);

    try {
      const customerRes = await fetch("http://127.0.0.1:8000/customers", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });
      const customer = await customerRes.json();

      var encounterId;
      const encounterRes = await fetch("http://127.0.0.1:8000/encounters", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ customer_id: customer.customer_id })
      });
      const encounter = await encounterRes.json();
      encounterId = encounter.encounter_id;
      setEncounterId(encounterId);

      const symptomRes = await fetch("http://127.0.0.1:8000/symptoms", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
              encounter_id: encounterId,
              symptoms: input
          })
      });
      const data = await symptomRes.json();

      const aiMessage = {
        role: 'assistant',
        content: data?.content || 'No diagnosis returned.',
      };

      setMessages((prev) => [...prev, aiMessage]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: 'Error retrieving diagnosis.' },
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = () => setOpenDialog(true);

  const handleAskAgain = () => {
    setMessages([]);
    setInput('');
    setLoading(false);
    setIsSaved(false);
  };

  const handleConfirmSave = async () => {
    await fetch('http://127.0.0.1:8000/encounters/fhir', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ encounter_id: encounterId, patientName, birthDate }),
    });

    setOpenDialog(false);
    setPatientName('');
    setBirthDate('');
    setIsSaved(true);
  };

  return (
    <ThemeProvider theme={theme}>
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default', overflowY: 'auto' }}>
        <Typography
          variant="h5"
          sx={{
            position: 'fixed',
            top: 20,
            left: 30,
            zIndex: 1000,
          }}
        >
          Barca
        </Typography>

        <Container
          maxWidth="lg"
          sx={{
            paddingTop: 8,
            paddingBottom: 4,
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            justifyContent: messages.length === 0 ? 'center' : 'flex-start',
            alignItems: 'center',
            px: 2,
          }}
        >
          {messages.length === 0 && (
            <Box
              sx={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 3,
                width: '100%',
              }}
            >
              <Typography variant="h4">How are you feeling?</Typography>

              <Paper
                elevation={3}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  px: 2,
                  py: 1,
                  borderRadius: '999px',
                  width: '100%',
                  maxWidth: 600,
                }}
              >
                <TextField
                  fullWidth
                  variant="standard"
                  placeholder="Describe your symptoms..."
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleSubmit()}
                  slotProps={{
                    input: {
                      disableUnderline: true,
                    },
                  }}
                />
                <IconButton color="default" onClick={handleSubmit}>
                  <SendIcon />
                </IconButton>
              </Paper>
            </Box>
          )}

          {messages.map((msg, index) => (
            <Box
              key={index}
              sx={{
                width: '100%',
                display: 'flex',
                justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
                mb: 2,
              }}
            >
              <Paper
                sx={{
                  p: 2,
                  maxWidth: '100%',
                  bgcolor: msg.role === 'user' ? 'secondary.main' : 'primary.main',
                  color: 'white',
                  fontFamily: 'Open Sans',
                  '& h3': { mt: 2, mb: 1, fontSize: '1.1rem', fontWeight: 700 },
                  '& p': { mb: 1, lineHeight: 1.6 },
                  '& ul, & ol': { mb: 1, pl: 2 },
                  '& li': { mb: 0.5 },
                  '& strong': { fontWeight: 600 },
                }}
              >
                {msg.role === 'user' ? (
                  msg.content
                ) : (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                )}
              </Paper>
            </Box>
          ))}

          {loading && (
            <Box
              sx={{
                width: '100%',
                display: 'flex',
                justifyContent: 'flex-start',
                alignItems: 'center',
                gap: 2,
                mb: 2,
              }}
            >
              <CircularProgress size={20} />
              <Typography>Analyzing symptoms...</Typography>
            </Box>
          )}
        </Container>

        {!loading && messages.length > 1 && (
          <Box
            sx={{
              position: 'fixed',
              bottom: 0,
              left: 0,
              right: 0,
              display: 'flex',
              gap: 2,
              justifyContent: 'center',
              alignItems: 'center',
              py: 2,
              px: 2,
              bgcolor: 'background.paper',
              borderTop: '1px solid',
              borderColor: 'divider',
            }}
          >
            <Button variant="contained" color="secondary" onClick={handleAskAgain}>
              Ask Again
            </Button>
            <Button variant="contained" color="primary" onClick={handleSave} disabled={isSaved}>
              {isSaved ? 'Encounter Saved' : 'Save Encounter'}
            </Button>
          </Box>
        )}

        <Backdrop open={openDialog} sx={{ zIndex: 1200 }} />

        <Dialog open={openDialog} onClose={() => setOpenDialog(false)}>
          <DialogTitle>Save Encounter</DialogTitle>
          <DialogContent>
            <TextField
              margin="dense"
              label="Name"
              fullWidth
              color="secondary"
              value={patientName}
              onChange={(e) => setPatientName(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
            <TextField
              margin="dense"
              label="Birth Date"
              type="date"
              color="secondary"
              fullWidth
              value={birthDate}
              onChange={(e) => setBirthDate(e.target.value)}
              slotProps={{ inputLabel: { shrink: true } }}
            />
          </DialogContent>
          <DialogActions>
            <Button variant="contained" color="secondary" onClick={() => setOpenDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleConfirmSave} variant="contained">
              Save
            </Button>
          </DialogActions>
        </Dialog>
      </Box>
    </ThemeProvider>
  );
}
