import React, {useState} from "react";

import TextField from "@material-ui/core/TextField";
import Grid from "@material-ui/core/Grid";
import Paper from "@material-ui/core/Paper";
import Button from "@material-ui/core/Button";
import Typography from "@material-ui/core/Typography";
import {makeStyles} from "@material-ui/core/styles";
import Snackbar from "@material-ui/core/Snackbar";
import Alert from "@material-ui/lab/Alert";
import {useQuery} from "../../utils";

const useStyles = makeStyles((theme) => ({
  root: {
    flexShrink: 0,
  },
  paper: {
    padding: theme.spacing(2)
  }
}));


export default function Login() {
  const classes = useStyles();
  const [alertOpen, setAlertOpen] = useState(useQuery().get('error') !== null);

  return (
    <Grid
      container
      spacing={2}
      direction="column"
      justify="center"
      alignItems="center"
    >
      <Grid item xs={12}>
        <Snackbar open={alertOpen} autoHideDuration={6000} onClose={() => setAlertOpen(false)}>
          <Alert onClose={() => setAlertOpen(false)} severity="error">
            {useQuery().get('error')}
          </Alert>
        </Snackbar>
      </Grid>
      <Grid item xs={12}>
        <Paper className={classes.paper}>
          <Typography variant={"h4"}>Login</Typography>
          <form className={classes.root} noValidate autoComplete="off" method={"GET"} action="/api/public/login">
            <Grid container spacing={2} direction={"column"} justify={"center"} alignItems={"center"}>
              <Grid item xs={12}>
                <TextField id="username" name="username" label="Username" variant="outlined"/>
              </Grid>
              <Grid item xs={12}>
                <TextField id="password" name="password" label="password" variant="outlined" type="password"/>
              </Grid>
              <Grid item xs={12}>
                <Button variant="contained" color="primary" type="submit">
                  Submit
                </Button>
              </Grid>
            </Grid>
          </form>
        </Paper>
      </Grid>
    </Grid>
  )
}