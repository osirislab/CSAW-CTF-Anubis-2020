import React, {useState} from "react";
import AceEditor from "react-ace";
import "ace-builds/src-noconflict/mode-c_cpp";
import "ace-builds/src-noconflict/theme-monokai";
import "ace-builds/src-noconflict/ext-language_tools";
import {makeStyles} from "@material-ui/core/styles";
import Paper from '@material-ui/core/Paper';
import Grid from "@material-ui/core/Grid";
import Button from "@material-ui/core/Button";
import CircularProgress from "@material-ui/core/CircularProgress";
import {Redirect} from "react-router-dom";
import useGet from "../../useGet";
import {useQuery} from "../../utils";


const useStyles = makeStyles((theme) => ({
  root: {
    flexShrink: 0,
  },
  paper: {
    padding: theme.spacing(2),
    margin: theme.spacing(5),
    minWidth: 700,
  }
}));

export default function SubmissionEditor() {
  const classes = useStyles();
  const assignment = useQuery().get('assignment');
  const [code, setCode] = useState(null);
  const {data, loading, error} = useGet(`/api/public/current-code/${assignment}`);

  if (loading) return <CircularProgress/>;
  if (error) return <Redirect to={`/error`}/>

  if (code === null) {
    setCode(data.code);
  }

  return (
    <Grid
      container
      spacing={2}
      direction="column"
      justify="center"
      alignItems="center"
    >
      <Grid item xs={12}>
        <Paper className={classes.paper}>
          <Grid
            container
            spacing={2}
            direction="column"
            justify="center"
            alignItems="center"
          >
            <Grid item xs={12}>
              <AceEditor
                mode="c_cpp"
                theme="monokai"
                value={code}
                width={700}
                height={750}
                onChange={_code => setCode(_code)}
              />
            </Grid>
            <Grid item xs={12}>
              <form
                className={classes.root}
                noValidate
                autoComplete="off"
                method={"POST"}
                action={`/api/public/submit/${assignment}`}
              >
                <textarea name="code" value={code} hidden/>
                <Button variant={"contained"} color={"primary"} type={"submit"}>Submit</Button>
              </form>
            </Grid>
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  )
}
