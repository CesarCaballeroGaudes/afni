/*****************************************************************************
   Major portions of this software are copyrighted by the Medical College
   of Wisconsin, 1994-2001, and are released under the Gnu General Public
   License, Version 2.  See the file README.Copyright for details.
******************************************************************************/

/*---------------------------------------------------------------------------*/
/*
  Program to correct for image intensity nonuniformity.

  File:    3dUniformize.c
  Author:  B. Douglas Ward
  Date:    28 January 2000

  Mod:     Added call to AFNI_logger.
  Date:    15 August 2001

*/

/*---------------------------------------------------------------------------*/

#define PROGRAM_NAME "3dUniformize"                  /* name of this program */
#define PROGRAM_AUTHOR "B. D. Ward"                        /* program author */
#define PROGRAM_INITIAL "28 January 2000" /* date of initial program release */
#define PROGRAM_LATEST  "03 January 2010 [zss]" /* date of latest program revision */

/*---------------------------------------------------------------------------*/
/*
  Include header files.
*/

#include "mrilib.h"
#include "matrix.h"


/*---------------------------------------------------------------------------*/
/*
  Global variables, constants, and data structures.
*/

#define MAX_STRING_LENGTH THD_MAX_NAME

static THD_3dim_dataset * anat_dset = NULL;     /* input anatomical dataset  */
char * commandline = NULL ;                /* command line for history notes */

int input_datum = MRI_short ;              /* 16 Apr 2003 - RWCox */
int quiet       = 0 ;                      /* ditto */
#define USE_QUIET

typedef struct UN_options
{
  char * anat_filename;       /* file name for input anat dataset */
  char * prefix_filename;     /* prefix name for output dataset */
  Boolean quiet;              /* flag for suppress screen output */
  int lower_limit;    /* lower limit for voxel intensity */
  int upper_limit;    /* upper limit for voxel intensity 0 for ignoring this parameter*/
  int rpts;           /* #voxels in sub-sampled image (for pdf) */
  int spts;           /* #voxels in subsub-sampled image (for field poly.) */
  int nbin;           /* #bins for pdf estimation */
  int npar;           /* #parameters for field polynomial */
  int niter;          /* #number of iterations */
  THD_3dim_dataset * new_dset;   /* output afni data set pointer */
} UN_options;


/*---------------------------------------------------------------------------*/
/*
  Include source code files.
*/

#include "estpdf3.c"


/*---------------------------------------------------------------------------*/
/*
   Print error message and stop.
*/

void UN_error (char * message)
{
  fprintf (stderr, "%s Error: %s \n", PROGRAM_NAME, message);
  exit(1);
}


/*---------------------------------------------------------------------------*/

/** macro to test a malloc-ed pointer for validity **/

#define MTEST(ptr) \
if((ptr)==NULL) \
( UN_error ("Cannot allocate memory") )


/*---------------------------------------------------------------------------*/
/*
   Routine to display 3dUniformize help menu.
*/

void display_help_menu()
{
  printf
    (
     "   ***** NOTES *********************************************\n"
     "   1) This program is superseded by 3dUnifize, and we don't\n"
     "      recommend that you use it.\n"
     "   2) This program will crash if you give it a multi-volume\n"
     "      dataset.\n"
     "   3) Neither 3dUniformize nor 3dUnifize can properly deal\n"
     "      with EPI datasets at this time.\n"
     "   *********************************************************\n"
     "\n"
     "This program corrects for T1-weighted image intensity nonuniformity.\n\n"
     "\n"
     "Usage: \n"
     "3dUniformize  \n"
     "-anat filename    Filename of anat dataset to be corrected            \n"
     "                                                                      \n"
     "[-clip_low LOW]   Use LOW as the voxel intensity separating           \n"
     "                  brain from air.                                     \n"
     "   NOTE: The historic clip_low value was 25.                          \n"
     "      But that only works for certain types of input data and can     \n"
     "      result in bad output depending on the range of values in        \n"
     "      the input dataset.                                              \n"
     "      The new default sets -clip_low via -auto_clip option.           \n"
     "[-clip_high HIGH] Do not include voxels with intensity higher         \n"
     "                  than HIGH in calculations.                          \n"
     "[-auto_clip]      Automatically set the clip levels.                  \n"
     "                  LOW in a procedure similar to 3dClipLevel,          \n"
     "                  HIGH is set to 3*LOW. (Default since Jan. 2011)     \n"
     "[-niter NITER]    Set the number of iterations for concentrating PDF  \n"
     "                  Default is 5.                                       \n"
     "[-quiet]          Suppress output to screen                           \n"
     "                                                                      \n"
     "-prefix pname     Prefix name for file to contain corrected image     \n"
     "\n"
     "Versions of this program postdating Jan. 3rd 2010 can handle byte, short\n"
     "or float input and output the result in the data type as the input\n"
      );

  printf("\n" MASTER_SHORTHELP_STRING ) ;
  PRINT_COMPILE_DATE ; exit(0);
}


/*---------------------------------------------------------------------------*/
/*
  Routine to initialize the input options.
*/

void initialize_options
(
  UN_options * option_data    /* uniformization program options */
)

{

  /*----- initialize default values -----*/
  option_data->anat_filename = NULL;    /* file name for input anat dataset */
  option_data->prefix_filename = NULL;  /* prefix name for output dataset */
  option_data->quiet = FALSE;           /* flag for suppress screen output */
  option_data->lower_limit = -1;        /* voxel intensity lower limit,
                                           used to be 25
                                           -1 is default flag for auto_clip
                                                       ZSS Jan 2011 */
  option_data->upper_limit = 0;
  option_data->rpts = 200000;   /* #voxels in sub-sampled image (for pdf) */
  option_data->spts = 10000;    /* #voxels in subsub-sampled image
                       (for field polynomial estimation) */
  option_data->nbin = 250;      /* #bins for pdf estimation */
  option_data->npar = 35;       /* #parameters for field polynomial */
  option_data->niter = 5;       /* #number of iterations  */
  option_data->new_dset = NULL;
}


/*---------------------------------------------------------------------------*/
/*
  Routine to get user specified input options.
*/

void get_options
(
  int argc,                        /* number of input arguments */
  char ** argv,                    /* array of input arguments */
  UN_options * option_data         /* uniformization program options */
)

{
  int nopt = 1;                     /* input option argument counter */
  int ival, index;                  /* integer input */
  float fval;                       /* float input */
  char message[MAX_STRING_LENGTH];  /* error message */


  /*----- does user request help menu? -----*/
  if (argc < 2 || strncmp(argv[1], "-help", 5) == 0)  display_help_menu();


  /*----- add to program log -----*/
  AFNI_logger (PROGRAM_NAME,argc,argv);


  /*----- main loop over input options -----*/
  while (nopt < argc )
    {

      /*-----   -anat filename   -----*/
      if (strncmp(argv[nopt], "-anat", 5) == 0)
     {
       nopt++;
       if (nopt >= argc)  UN_error ("need argument after -anat ");
       option_data->anat_filename =
         malloc (sizeof(char) * MAX_STRING_LENGTH);
       MTEST (option_data->anat_filename);
       strcpy (option_data->anat_filename, argv[nopt]);

       anat_dset = THD_open_dataset (option_data->anat_filename);
       if (!ISVALID_3DIM_DATASET (anat_dset))
         {
           sprintf (message, "Can't open dataset: %s\n",
                 option_data->anat_filename);
           UN_error (message);
         }
       DSET_load(anat_dset) ; CHECK_LOAD_ERROR(anat_dset) ;

     if( DSET_NVALS(anat_dset) > 1 )
      WARNING_message("3dUniformize cannot process multi-volume datasets :(") ;

      /* if input is not float, float it */
     input_datum = DSET_BRICK_TYPE(anat_dset,0);
     if( input_datum != MRI_float ){
         THD_3dim_dataset *qset ;
         register float *far ;
         register int ii,nvox ;
         MRI_IMAGE *imf=NULL;

         INFO_message("converting input dataset to float") ;
         qset = EDIT_empty_copy(anat_dset) ;
         nvox = DSET_NVOX(anat_dset) ;
         imf = THD_extract_float_brick(0,anat_dset) ;
         far = (float *)malloc(sizeof(float)*nvox) ;
         memcpy(far, MRI_FLOAT_PTR(imf), sizeof(float)*nvox) ;
         mri_free(imf); imf=NULL;
         EDIT_substitute_brick( qset , 0 , MRI_float, far);
         DSET_delete(anat_dset) ; anat_dset = qset ;
     }


     nopt++;
       continue;
     }

      /*-----   -clip_low  -----*/
      if (strncmp(argv[nopt], "-clip_low", 9) == 0)
     {
       nopt++;
       if (nopt >= argc)  UN_error ("need value after -clip_low ");
     /* compare with -1 noted by A Waite     29 Jul 2011 [rickr] */
     if (option_data->lower_limit >= 0) {
      UN_error ("lower clip value already set, check your options");
     }
     option_data->lower_limit = atoi(argv[nopt]); /* ZSS Sept 26 05 */
       nopt++;
       continue;
     }

      /*-----   -clip_high  -----*/
      if (strncmp(argv[nopt], "-clip_high", 9) == 0)
     {
       nopt++;
       if (nopt >= argc)  UN_error ("need value after -clip_high ");
     if (option_data->upper_limit) {
      UN_error ("upper clip value already set, check your options");
     }
     option_data->upper_limit = atoi(argv[nopt]); /* ZSS Sept 26 05 */
       nopt++;
       continue;
     }

   if (strncmp(argv[nopt], "-auto_clip", 8) == 0)
     {
     if (option_data->lower_limit >= 0) {
      UN_error ("lower clip value already set, check your options");
     }
     option_data->lower_limit = -1; /* flag for auto_clip ZSS Sept 26 05 */
       nopt++;
       continue;
     }

   if (strncmp(argv[nopt], "-niter", 6) == 0)
     {
     nopt++;
       if (nopt >= argc)  UN_error ("need value after -niter ");
     option_data->niter = atoi(argv[nopt]); /* flag for auto_clip ZSS Sept 26 05 */
       nopt++;
       continue;
     }

      /*-----   -quiet  -----*/
      if (strncmp(argv[nopt], "-quiet", 6) == 0)
     {
       option_data->quiet = TRUE;
          quiet = 1 ;                /* 16 Apr 2003 */
       nopt++;
       continue;
     }


      /*-----   -prefix prefixname   -----*/
      if (strncmp(argv[nopt], "-prefix", 7) == 0)
     {
       nopt++;
       if (nopt >= argc)  UN_error ("need argument after -prefix ");
       option_data->prefix_filename =
         malloc (sizeof(char) * MAX_STRING_LENGTH);
       MTEST (option_data->prefix_filename);
       strcpy (option_data->prefix_filename, argv[nopt]);
       nopt++;
       continue;
     }


      /*----- unknown command -----*/
      sprintf(message,"Unrecognized command line option: %s\n", argv[nopt]);
      UN_error (message);

    }

   if (option_data->lower_limit < 0) { /* ZSS Sept 26 05 */
      option_data->lower_limit = (int) THD_cliplevel( DSET_BRICK(anat_dset,0) , 0.0 ) ;
      option_data->upper_limit = 3*option_data->lower_limit;
      if (!quiet) {
         printf ( "\n"
                  "Lower limit set with THD_cliplevel at %d\n"
                  "Upper limit set to %d\n", option_data->lower_limit, option_data->upper_limit);
      }
   } else if (option_data->lower_limit == 0) {
      option_data->lower_limit = 25; /* The olde value */
      if (!quiet) {
         if (!option_data->upper_limit) {
            printf ( "\n"
                  "Lower limit set to historic default of %d\n"
                  "No upper limit used.\n", option_data->lower_limit);
         } else {
            printf ( "\n"
                  "Lower limit set to historic default of %d\n"
                  "Upper limit set to %d.\n", option_data->lower_limit, option_data->upper_limit);
         }
         printf ( "\n"
               "WARNING:\n"
               "Using the default clip value of 25\n"
               "might cause bad output depending\n"
               "on the range of values in your input\n"
               "dataset.\n"
               "You are better off using -auto_clip\n"
               "or -clip_low options instead.\n"
               "\n" );
      }
   } else {
      if (!quiet) {
         if (option_data->upper_limit) {
            printf ( "\n"
                  "Lower limit set by user to %d\n"
                  "Upper limit set to %d\n", option_data->lower_limit, option_data->upper_limit);
         } else {
            printf ( "\n"
                  "Lower limit set by user to %d\n"
                  "Upper limit not set.\n", option_data->lower_limit);
         }
      }
   }


}


/*---------------------------------------------------------------------------*/
/*
  Routine to check whether one output file already exists.
*/

void check_one_output_file
(
  char * filename                   /* name of output file */
)

{
  char message[MAX_STRING_LENGTH];    /* error message */
  THD_3dim_dataset * new_dset=NULL;   /* output afni data set pointer */
  int ierror;                         /* number of errors in editing data */


  /*----- make an empty copy of input dataset -----*/
  new_dset = EDIT_empty_copy ( anat_dset );


  ierror = EDIT_dset_items( new_dset ,
                   ADN_prefix , filename ,
                   ADN_label1 , filename ,
                   ADN_self_name , filename ,
                   ADN_none ) ;

  if( ierror > 0 )
    {
      sprintf (message,
            "*** %d errors in attempting to create output dataset!\n",
            ierror);
      UN_error (message);
    }

  if( THD_deathcon() && THD_is_file(new_dset->dblk->diskptr->header_name) )
    {
      sprintf (message,
            "Output dataset file %s already exists"
            "--cannot continue!\a\n",
            new_dset->dblk->diskptr->header_name);
      UN_error (message);
    }

  /*----- deallocate memory -----*/
  THD_delete_3dim_dataset( new_dset , False ) ; new_dset = NULL ;

}


/*---------------------------------------------------------------------------*/

void verify_inputs
(
  UN_options * option_data         /* uniformization program options */
)

{
  char *filename;
  int ierror;

  filename = option_data->prefix_filename;
  /*-- make an empty copy of this dataset, for eventual output --*/
  option_data->new_dset =  EDIT_empty_copy( anat_dset ) ;

  /* check if output name is OK */
  ierror = EDIT_dset_items( option_data->new_dset ,
                   ADN_prefix , filename ,
                   ADN_label1 , filename ,
                   ADN_self_name , filename ,
                   ADN_none ) ;
  if( ierror > 0 ){
    fprintf(stderr,
         "*** %d errors in attempting to create output dataset!\n",
         ierror ) ;
    exit(1) ;
  }


  if( THD_deathcon() && THD_is_file(option_data->new_dset->dblk->diskptr->header_name) ){
    fprintf(stderr,
         "*** Output dataset file %s already exists--cannot continue!\a\n",
         option_data->new_dset->dblk->diskptr->header_name ) ;
    exit(1) ;
  }



}


/*---------------------------------------------------------------------------*/
/*
  Program initialization.
*/

void initialize_program
(
  int argc,                        /* number of input arguments */
  char ** argv,                    /* array of input arguments */
  UN_options ** option_data,       /* uniformization program options */
  float ** ffim                    /* output image volume */
)

{
  int nxyz;                        /* #voxels in input dataset */


  /*----- Save command line for history notes -----*/
  commandline = tross_commandline( PROGRAM_NAME , argc,argv ) ;


  /*----- Allocate memory for input options -----*/
  *option_data = (UN_options *) malloc (sizeof(UN_options));
  MTEST (*option_data);


  /*----- Initialize the input options -----*/
  initialize_options (*option_data);


  /*----- Get operator inputs -----*/
  get_options (argc, argv, *option_data);


  /*----- Verify that inputs are acceptable -----*/
  verify_inputs (*option_data);


  /*----- Initialize random number generator -----*/
  rand_initialize (1234567);


  /*----- Allocate memory for output volume -----*/
  nxyz = DSET_NX(anat_dset) * DSET_NY(anat_dset) * DSET_NZ(anat_dset);
  *ffim = (float *) calloc (nxyz, sizeof(float));
  MTEST (*ffim);
}


/*---------------------------------------------------------------------------*/
/*
  Write time series data to specified file.
*/

void ts_write (char * filename, int ts_length, float * data)
{
  int it;
  FILE * outfile = NULL;

  outfile = fopen (filename, "w");


  for (it = 0;  it < ts_length;  it++)
    {
      fprintf (outfile, "%f ", data[it]);
      fprintf (outfile, " \n");
    }

  fclose (outfile);
}


/*---------------------------------------------------------------------------*/
/*
  Resample the original image at randomly selected voxels (whose intensity
  value is greater than the specified lower limit, to exclude voxels outside
  the brain).  Take the logarithm of the intensity values for the selected
  voxels.
*/

void resample
(
  UN_options * option_data,
  int * ir,                         /* voxel indices for resampled image */
  float * vr                        /* resampled image data (logarithms) */
)

{
  float * anat_data = NULL;
  int nxyz;
  int rpts;
  int lower_limit;
  int it, k;


  /*----- Initialize local variables -----*/
  nxyz = DSET_NX(anat_dset) * DSET_NY(anat_dset) * DSET_NZ(anat_dset);
  anat_data = (float *) DSET_BRICK_ARRAY(anat_dset,0);
  lower_limit = option_data->lower_limit;
  rpts = option_data->rpts;

  it = 0;
  while (it < rpts)
    {
      k = rand_uniform (0, nxyz);
      /* okay if no upper_limit, or data < upper_limit   16 Dec 2005 [rickr] */
      if ( (k >= 0) && (k < nxyz) && (anat_data[k] > lower_limit) &&
           ( ! option_data->upper_limit ||
               (anat_data[k] < option_data->upper_limit) ) )
     {
       ir[it] = k;
       vr[it] = log (anat_data[k] + rand_uniform (0.0,1.0));
       it++;
     }
    }

  return;
}


/*---------------------------------------------------------------------------*/
/*
  Create intensity map that will tend to concentrate values around the
  means of the gray and white matter distributions.
*/

void create_map (pdf vpdf, float * pars, float * vtou)

{
  int ibin;
  float v;

  for (ibin = 0;  ibin < vpdf.nbin;  ibin++)
    {
      v = PDF_ibin_to_xvalue (vpdf, ibin);

      if ((v > pars[4]-2.0*pars[5]) && (v < 0.5*(pars[4]+pars[7])))
     vtou[ibin] = pars[4];
      else if ((v > 0.5*(pars[4]+pars[7])) && (v < pars[7]+2.0*pars[8]))
     vtou[ibin] = pars[7];
      else
     vtou[ibin] = v;

    }

}


/*---------------------------------------------------------------------------*/
/*
  Use the intensity map to transform values of voxel intensities.
*/

void map_vtou (pdf vpdf, int rpts, float * vr, float * vtou, float * ur)

{
  int i, ibin;
  float v;


  for (i = 0;  i < rpts;  i++)
    {
      v = vr[i];
      ibin = PDF_xvalue_to_ibin (vpdf, v);

      if ((ibin >= 0) && (ibin < vpdf.nbin))
     ur[i] = vtou[ibin];
      else
     ur[i] = v;
    }

}


/*---------------------------------------------------------------------------*/

void subtract (int rpts, float * a, float * b, float * c)

{
  int i;


  for (i = 0;  i < rpts;  i++)
    {
      c[i] = a[i] - b[i];
    }

}


/*---------------------------------------------------------------------------*/
/*
  Create one row of the X matrix.
*/

void create_row (int ixyz, int nx, int ny, int nz, float * xrow)

{
  int ix, jy, kz;
  float x, y, z, x2, y2, z2, x3, y3, z3, x4, y4, z4;


  IJK_TO_THREE (ixyz, ix, jy, kz, nx, nx*ny);


  x = (float) ix / (float) nx - 0.5;
  y = (float) jy / (float) ny - 0.5;
  z = (float) kz / (float) nz - 0.5;

  x2 = x*x;   x3 = x*x2;   x4 = x2*x2;
  y2 = y*y;   y3 = y*y2;   y4 = y2*y2;
  z2 = z*z;   z3 = z*z2;   z4 = z2*z2;


  xrow[0] = 1.0;
  xrow[1] = x;
  xrow[2] = y;
  xrow[3] = z;
  xrow[4] = x*y;
  xrow[5] = x*z;
  xrow[6] = y*z;
  xrow[7] = x2;
  xrow[8] = y2;
  xrow[9] = z2;
  xrow[10] = x*y*z;
  xrow[11] = x2*y;
  xrow[12] = x2*z;
  xrow[13] = y2*x;
  xrow[14] = y2*z;
  xrow[15] = z2*x;
  xrow[16] = z2*y;
  xrow[17] = x3;
  xrow[18] = y3;
  xrow[19] = z3;
  xrow[20] = x2*y*z;
  xrow[21] = x*y2*z;
  xrow[22] = x*y*z2;
  xrow[23] = x2*y2;
  xrow[24] = x2*z2;
  xrow[25] = y2*z2;
  xrow[26] = x3*y;
  xrow[27] = x3*z;
  xrow[28] = x*y3;
  xrow[29] = y3*z;
  xrow[30] = x*z3;
  xrow[31] = y*z3;
  xrow[32] = x4;
  xrow[33] = y4;
  xrow[34] = z4;


  return;
}


/*---------------------------------------------------------------------------*/
/*
  Approximate the distortion field with a polynomial function in 3 dimensions.
*/

void poly_field (int nx, int ny, int nz, int rpts, int * ir, float * fr,
           int spts, int npar, float * fpar)

{
  int p;                   /* number of parameters in the full model */
  int i, j, k;
  matrix x;                      /* independent variable matrix */
  matrix xtxinv;                 /* matrix:  1/(X'X)       */
  matrix xtxinvxt;               /* matrix:  (1/(X'X))X'   */
  vector y;
  vector coef;
  float * xrow = NULL;
  int ip;
  int iter;
  float f;


  p = npar;


  /*----- Initialize matrices and vectors -----*/
  matrix_initialize (&x);
  matrix_initialize (&xtxinv);
  matrix_initialize (&xtxinvxt);
  vector_initialize (&y);
  vector_initialize (&coef);


  /*----- Allocate memory -----*/
  matrix_create (spts, p, &x);
  vector_create (spts, &y);
  xrow = (float *) malloc (sizeof(float) * p);


  /*----- Set up the X matrix and Y vector -----*/
  for (i = 0;  i < spts;  i++)
    {
      k = rand_uniform (0, rpts);
      create_row (ir[k], nx, ny, nz, xrow);

      for (j = 0;  j < p;  j++)
     x.elts[i][j] = xrow[j];
      y.elts[i] = fr[k];
    }


  /*
      matrix_sprint ("X matrix = ", x);
      vector_sprint ("Y vector = ", y);
  */


  {
    /*----- calculate various matrices which will be needed later -----*/
    matrix xt, xtx;            /* temporary matrix calculation results */
    int ok;                    /* flag for successful matrix inversion */


    /*----- initialize matrices -----*/
    matrix_initialize (&xt);
    matrix_initialize (&xtx);

    matrix_transpose (x, &xt);
    matrix_multiply (xt, x, &xtx);
    ok = matrix_inverse (xtx, &xtxinv);

    if (ok)
      matrix_multiply (xtxinv, xt, &xtxinvxt);
    else
      {
     matrix_sprint ("X matrix = ", x);
     matrix_sprint ("X'X matrix = ", xtx);
     UN_error ("Improper X matrix  (cannot invert X'X) ");
      }

    /*----- dispose of matrices -----*/
    matrix_destroy (&xtx);
    matrix_destroy (&xt);

  }


  /*
    matrix_sprint ("1/(X'X)     = ", xtxinv);
    matrix_sprint ("(1/(X'X))X' = ", xtxinvxt);
    vector_sprint ("Y data  = ", y);
  */

  vector_multiply (xtxinvxt, y, &coef);
  /*
    vector_sprint ("Coef    = ", coef);
  */


  for (ip = 0;  ip < p;  ip++)
    {
     fpar[ip] = coef.elts[ip];
    }


  /*----- Dispose of matrices and vectors -----*/
  matrix_destroy (&x);
  matrix_destroy (&xtxinv);
  matrix_destroy (&xtxinvxt);
  vector_destroy (&y);
  vector_destroy (&coef);


}


/*---------------------------------------------------------------------------*/
/*
  Use the 3-dimensional polynomial function to estimate the distortion field
  at each point.
*/

float warp_image (int npar, float * fpar, int nx, int ny, int nz,
            int rpts, int * ir, float * fs)
{
  int i, j;
  float x;
  float * xrow;
  float max_warp;


  xrow = (float *) malloc (sizeof(float) * npar);


  max_warp = 0.0;

  for (i = 0;  i < rpts;  i++)
    {
      create_row (ir[i], nx, ny, nz, xrow);

      fs[i] = 0.0;

      for (j = 1;  j < npar;  j++)
     fs[i] += fpar[j] * xrow[j];

      if (fabs(fs[i]) > max_warp)
     max_warp = fabs(fs[i]);
    }


  free (xrow);   xrow = NULL;


  return (max_warp);
}


/*---------------------------------------------------------------------------*/
/*
  Find polynomial approximation to the distortion field.
*/

void estimate_field (UN_options * option_data,
               int * ir, float * vr, float * fpar)
{
  float * ur = NULL, * us = NULL, * fr = NULL, * fs = NULL, * wr = NULL;
  float * vtou = NULL;
  float * gpar;
  int iter = 0, itermax=5;
  int ip;
  int it;
  int nx, ny, nz, nxy, nxyz;
  int rpts, spts, nbin, npar;
  float parameters [DIMENSION];    /* parameters for PDF estimation */
  Boolean ok = TRUE;               /* flag for successful PDF estimation */
  char filename[MAX_STRING_LENGTH];


  /*----- Initialize local variables -----*/
  nx = DSET_NX(anat_dset);  ny = DSET_NY(anat_dset);  nz = DSET_NZ(anat_dset);
  nxy = nx*ny;   nxyz = nxy*nz;
  rpts = option_data->rpts;
  spts = option_data->spts;
  nbin = option_data->nbin;
  npar = option_data->npar;
  itermax = option_data->niter;


  /*----- Allocate memory -----*/
  ur   = (float *) malloc (sizeof(float) * rpts);   MTEST (ur);
  us   = (float *) malloc (sizeof(float) * rpts);   MTEST (us);
  fr   = (float *) malloc (sizeof(float) * rpts);   MTEST (fr);
  fs   = (float *) malloc (sizeof(float) * rpts);   MTEST (fs);
  wr   = (float *) malloc (sizeof(float) * rpts);   MTEST (wr);
  gpar = (float *) malloc (sizeof(float) * npar);   MTEST (gpar);
  vtou = (float *) malloc (sizeof(float) * nbin);   MTEST (vtou);


  /*----- Initialize polynomial coefficients -----*/
  for (ip = 0;  ip < npar;  ip++)
    {
      fpar[ip] = 0.0;
      gpar[ip] = 0.0;
    }


  /*----- Estimate pdf for resampled data -----*/
  if( 0 && !quiet ){
   fprintf (stderr,"       PDF_Initializing... \n");
  }
  PDF_initialize (&p);
  if( 0 && !quiet ){
   fprintf (stderr,"       float to pdf... \n");
  }
  PDF_float_to_pdf (rpts, vr, nbin, &p);

  if( !quiet ){
   sprintf (filename, "p%d.1D", iter);
   fprintf (stderr,"       Writing pdf output to %s... \n", filename);
   PDF_write_file (filename, p);
  }


  /*----- Estimate gross field distortion -----*/
  if( 0 && !quiet ){
   fprintf (stderr,"       Estimating gross distortions... \n");
  }
  poly_field (nx, ny, nz, rpts, ir, vr, spts, npar, fpar);
  warp_image (npar, fpar, nx, ny, nz, rpts, ir, fs);
  subtract (rpts, vr, fs, ur);


  for (ip = 0;  ip < rpts;  ip++)
    vr[ip] = ur[ip];


  /*----- Iterate over field distortion for concentrating the PDF -----*/
  for (iter = 1;  iter <= itermax;  iter++)
    {
      /*----- Estimate pdf for perturbed image ur -----*/
      estpdf_float (rpts, ur, nbin, parameters);
      PDF_sprint ("p", p);
      if( !quiet ){
       sprintf (filename, "p%d.1D", iter);
       PDF_write_file (filename, p);
      }

      /*----- Sharpen the pdf and produce modified image wr -----*/
      create_map (p, parameters, vtou);
      if( !quiet ){
       sprintf (filename, "vtou%d.1D", iter);
       ts_write (filename, p.nbin, vtou);
      }
      map_vtou (p, rpts, ur, vtou, wr);

      /*----- Estimate smooth distortion field fs -----*/
      subtract (rpts, vr, wr, fr);
      poly_field (nx, ny, nz, rpts, ir, fr, spts, npar, gpar);
      warp_image (npar, gpar, nx, ny, nz, rpts, ir, fs);

      /*----- Create perturbed image ur -----*/
      subtract (rpts, vr, fs, ur);
    }


  /*----- Accumulate distortion field polynomial coefficients -----*/
  for (ip = 0;  ip < npar;  ip++)
    fpar[ip] += gpar[ip];


  /*----- Deallocate memory -----*/
  free (ur);     ur = NULL;
  free (us);     us = NULL;
  free (fr);     fr = NULL;
  free (fs);     fs = NULL;
  free (wr);     wr = NULL;
  free (gpar);   gpar = NULL;
  free (vtou);   vtou = NULL;


  return;
}


/*---------------------------------------------------------------------------*/
/*
  Remove the nonuniformity field.
*/

void remove_field (UN_options * option_data, float * fpar, float * ffim)
{
  float * anat_data = NULL;
  int rpts;
  int npar;
  int lower_limit;
  int nx, ny, nz, nxyz;
  int ixyz, jpar;
  float x;
  float * xrow;
  float f;


  /*----- Initialize local variables -----*/
  nx = DSET_NX(anat_dset);  ny = DSET_NY(anat_dset);  nz = DSET_NZ(anat_dset);
  nxyz = nx*ny*nz;
  anat_data = (float *) DSET_BRICK_ARRAY(anat_dset,0);
  rpts = option_data->rpts;
  npar = option_data->npar;
  lower_limit = option_data->lower_limit;

  xrow = (float *) malloc (sizeof(float) * npar);


  for (ixyz = 0;  ixyz < nxyz;  ixyz++)
    {
        {
          create_row (ixyz, nx, ny, nz, xrow);

          f = 0.0;
          for (jpar = 1;  jpar < npar;  jpar++)
            f += fpar[jpar] * xrow[jpar];

          ffim[ixyz] = exp( log(anat_data[ixyz]) - f);
        }

    }


  return;
}


/*---------------------------------------------------------------------------*/
/*
  Correct for image intensity nonuniformity.
*/

void uniformize (UN_options * option_data, float * ffim)

{
  int * ir = NULL;
  float * vr = NULL;
  float * fpar = NULL;
  int rpts, npar;


  /*----- Initialize local variables -----*/
  rpts = option_data->rpts;
  npar = option_data->npar;


  /*----- Allocate memory -----*/
  ir = (int *) malloc (sizeof(int) * rpts);         MTEST(ir);
  vr = (float *) malloc (sizeof(float) * rpts);     MTEST(vr);
  fpar = (float *) malloc (sizeof(float) * npar);   MTEST(fpar);


  /*----- Resample the data -----*/
  if( 0 && !quiet ){
   fprintf (stderr,"     resampling... \n");
  }
  resample (option_data, ir, vr);


  /*----- Estimate the nonuniformity field -----*/
  if( 0 && !quiet ){
   fprintf (stderr,"     estimating field... \n");
  }
  estimate_field (option_data, ir, vr, fpar);


  /*----- Remove the nonuniformity field -----*/
  if( 0 && !quiet ){
   fprintf (stderr,"     removing field... \n");
  }


  remove_field (option_data, fpar, ffim);


  /*----- Deallocate memory -----*/
  free (ir);     ir = NULL;
  free (vr);     vr = NULL;
  free (fpar);   fpar = NULL;

}


/*---------------------------------------------------------------------------*/
/*
  Routine to write one AFNI dataset.


*/

void write_afni_data
(
  UN_options * option_data,
  float * ffim
)

{
  int nxyz;                           /* number of voxels */
  int ii;                             /* voxel index */
  int ierror;                         /* number of errors in editing data */
  int ibuf[32];                       /* integer buffer */
  float fbuf[MAX_STAT_AUX];           /* float buffer */
  int output_datum;                   /* data type for output data */
  char * filename;                    /* prefix filename for output */
  byte *bfim = NULL ;                 /* 16 Apr 2003 */

  /*----- initialize local variables -----*/
  nxyz = DSET_NX(anat_dset) * DSET_NY(anat_dset) * DSET_NZ(anat_dset);


  /*----- Record history of dataset -----*/
  tross_Copy_History( anat_dset , option_data->new_dset ) ;
  if( commandline != NULL )
     tross_Append_History( option_data->new_dset , commandline ) ;


  /*----- deallocate memory -----*/
  THD_delete_3dim_dataset (anat_dset, False);   anat_dset = NULL ;

  output_datum = input_datum ;


  /*-- we now return control to your regular programming --*/
  ibuf[0] = output_datum ;

  ierror = EDIT_dset_items( option_data->new_dset ,
                   ADN_datum_array , ibuf ,
                   ADN_malloc_type, DATABLOCK_MEM_MALLOC ,
                   ADN_none ) ;


  if( ierror > 0 ){
    fprintf(stderr,
         "*** %d errors in attempting to create output dataset!\n",
         ierror ) ;
    exit(1) ;
  }


  if( THD_is_file(option_data->new_dset->dblk->diskptr->header_name) ){
    fprintf(stderr,
         "*** Output dataset file %s already exists--cannot continue!\a\n",
         option_data->new_dset->dblk->diskptr->header_name ) ;
    exit(1) ;
  }


  EDIT_substscale_brick(option_data->new_dset,0,
                        MRI_float,ffim , output_datum, -1.0 );

  THD_load_statistics( option_data->new_dset ) ;
  THD_write_3dim_dataset( NULL,NULL , option_data->new_dset , True ) ;


  /*----- deallocate memory -----*/
  THD_delete_3dim_dataset( option_data->new_dset , False ) ; option_data->new_dset = NULL ;

}


/*---------------------------------------------------------------------------*/
/*
  This is the main routine for program 3dUniformize.
*/

int main
(
  int argc,                /* number of input arguments */
  char ** argv             /* array of input arguments */
)

{
  UN_options * option_data = NULL;     /* uniformization program options */
  float * ffim = NULL;                 /* output uniformized image */


  { int ii ;                           /* 16 Apr 2003 */
    for( ii=1 ; ii < argc ; ii++ ){
      if( strcmp(argv[ii],"-quiet") == 0 ){ quiet = 1; break; }
    }
  }

  /*----- Identify software -----*/
#if 0
  if( !quiet ){
   printf ("\n\n");
   printf ("Program: %s \n", PROGRAM_NAME);
   printf ("Author:  %s \n", PROGRAM_AUTHOR);
   printf ("Initial Release:  %s \n", PROGRAM_INITIAL);
   printf ("Latest Revision:  %s \n", PROGRAM_LATEST);
   printf ("\n");
  }
#endif

   PRINT_VERSION("3dUniformize") ; AUTHOR(PROGRAM_AUTHOR);
   mainENTRY("3dUniformize main") ; machdep() ;


  /*----- Program initialization -----*/
  if( !quiet ){
   fprintf (stderr,"  Initializing... \n");
  }
  initialize_program (argc, argv, &option_data, &ffim);

  WARNING_message(" ") ;
  WARNING_message("Please use 3dUnifize instead of 3dUniformize!") ;
  WARNING_message(" ") ;


  /*----- Perform uniformization -----*/

  if( !quiet ){
   fprintf (stderr,"  Uniformizing... \n");
  }
  uniformize (option_data, ffim);


  /*----- Write out the results -----*/
  if( !quiet ){
   fprintf (stderr,"  Writing results... \n");
  }
  write_afni_data (option_data, ffim);


  exit(0);

}

/*---------------------------------------------------------------------------*/






