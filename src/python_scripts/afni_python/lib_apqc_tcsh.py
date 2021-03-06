#
auth = 'PA Taylor'
# ver : 1.32 || date: Oct 15, 2018
# + some level of written-ness
#
# ver : 1.33 || date: Oct 16, 2018
# + new uvars
# + new checks
# + new QC dir and subdir defs
#
# ver : 1.34 || date: Oct 17, 2018
# + new uvars
# + new text, new output strings
# + WARN type introduced
#
#ver = '1.4' ; date = 'Oct 23, 2018'
# + do stats differently: separate olay and thr
# + also start a json for the pbar info
#
#ver = '1.5' ; date = 'Nov 1, 2018'
# + update regression warning 
#
#ver = '1.51' ; date = 'Nov 19, 2018'
# + update 1dplot string labels (add in "enorm" and "outliers")
#
#ver = '1.6' ; date = 'Dec 2, 2018'
# + check_dep() now has more conditions, because of some specific
#   vars+values that may or may not be there
#   - first one: for stats_dsets, check about "NO_STATS" value
#
#ver = '1.7' ; date = 'Dec 23, 2018'
# + [PT] put the censoring vertical color bars into the reg* 1D plots,
#        for both basic and pythonic styles
# + [PT] rename "run_mode" -> "run_style" (more specific/correct)
#
ver = '1.8' ; date = 'Jan 2, 2019'
# + [PT] add media_info
# + [PT] change order of enorm and outlier
# + [PT] add in EPI in orig space viewing
# + [PT] copy gen_ss JSON file into QC_*/media_info/
#
#########################################################################

import sys
import collections         as coll
import lib_apqc_html_helps as lahh
import lib_ss_review       as lssr

# ----------------------------------------------------------------------

scriptname = '@ss_review_html'
qcbase     = 'QC'                    # full odir has subj ID concatenated
dir_img    = 'media'
dir_info   = 'extra_info'            # for gen_ss- and AP-JSONs, and more

page_title_json = '__page_title'


# ----------------------------------------------------------------------

def check_dep(D, lcheck):
    '''Does dictionary 'D' contain each of the elements of 'lcheck'?'''

    HAS_ALL = 1
    for x in lcheck:

        # general check: based on existence
        if not(D.__contains__(x)) :
            HAS_ALL = 0
            break

        # ---- specific check(s), based on known values:

        # in this case, the $stats_dset var can contain essentially a
        # NULL value, NO_STATS, and that is reflected here
        elif x == "stats_dset" :
            if D[x] == "NO_STATS" :
                HAS_ALL = 0
                break

    return HAS_ALL

# ----------------------------------------------------------------------

def bannerize( x, fullwid=76, indent=0, padpre=1, padpost=2):
    '''Make the banner for each QC image block.  

Inputs
------
    x : a string that is the message to put, and it gets wrapped with a
        comment symbol and '='.

    fullwid : can be any number of width; default is 76 because there
        are 2 other characters put in: ' ' before/after the string.

    indent : number of spaces to prepend to the line, if desired

    padpre : number of empty lines to affix beforehand

    padpost : number of empty lines to affix after text

Returns
-------
    string : x padded with comment/lines/spaces.

    '''

    out = indent*' ' + "# "

    x = x.strip()
    freespace = fullwid - len(out) - len(x)

    if freespace < 0:
        freespace = 0

    lban = freespace // 2
    rban = freespace - lban
        
    out+= lban*"="
    out+= ' '+x+' '
    out+= rban*"="

    if padpre:
        out = padpre*'\n'+out
    if padpost:
        out+= padpost*'\n'

    return out

# ----------------------------------------------------------------------

def padassign(x, L):
    '''Move an assignment operator '=' rightward to a new index L, if it
exists to the left; if it exists to the right of that spot, or if it
doesn't appear in that string, just return the original string.  If
multiple occurences of '=' occur in a string, just return original.

    '''
    
    # check if string contains it
    if not('=' in x):
        return x

    # check if multiple occurences
    if x.count('=') > 1:
        return x

    # check if we are already there/rightward
    K = x.index('=')
    if K >= L:
        return x

    out = x.replace('=', (L-K)*' '+'=')

    return out

# ----------------------------------------------------------------------

def commandize( x, fullwid=76, indent=0, padpre=0, padpost=0,
                ALIGNASSIGN=False, ALLEOL=True, cmdindent=4,
                REP_TIL=True):
    '''Make the readable/spaced/EOL-char'ed version for each QC image
cmd.

Inputs
------

    x : a string that is the cmd; should arranged into multiple lines
        (for long commands). Don't need/shouldn't have EOL chars.

    fullwid : can be any number of width; default is 76, since ' \'
        gets added on to most lines.

    indent : number of spaces to prepend to each line, if desired

    padpre : number of empty lines to affix beforehand

    padpost : number of empty lines to affix after text

    ALIGNASSIGN : flag to line up assignment operators, using longest in
        list of commands

    ALLEOL : flag to use the EOL char at the end of all (but the last)
        lines;  if entering separate cmds, turn off.

    cmdindent : number of spaces to prepend to lines after the [0]th,
        i.e., just indenting within a single command.  Wouldn't be
        used if there are several sep lines, for example.

    REP_TIL : replace any tilde '~' with a space at the end (may be
        useful because the lines are stripped of surrounding white
        space to start)

Returns
-------

    string : will have the same number of lines as x, but all lines
    after [0]th will have indentation, and each line except [-1]th
    will have EOL char at end

    '''

    y = x.split('\n')
    Nlines = len(y)
    count = 0
    new = []
    maxia = 0    # will be loc of assign ops if using ALIGNASSIGN

    # go through, strip whitespace from ends, and find out where the
    # '=' are in each line
    z = []
    for line in y:
        ll = line.strip()
        if ALIGNASSIGN :
            if '=' in ll:
                iassign = ll.index('=')
                if iassign > maxia :
                    maxia = iassign
        z.append(ll)

    # line up assign ops if asked; also, need nonzero maxia
    if ALIGNASSIGN and maxia:
        for i in range(len(z)):
            z[i] = padassign(z[i], maxia)

    # go through last time and space everything appropriately
    for line in z:
        ll = line.strip()
        if len(ll) :
            ll = indent*' ' +ll
            if count:
                ll = cmdindent*' ' + ll
            if ALLEOL :
                lenll = len(ll)
                pad = fullwid - lenll
                if pad > 0:
                    ll+= pad*' '
            if REP_TIL:
                ll = ll.replace('~', ' ')
            new.append( ll )
            count+=1

    # put newlines at ends of each, or not
    if ALLEOL :
        out = ' \\\n'.join(new)
    else:
        out = '\n'.join(new)

    if padpre:
        out = padpre*'\n'+out
    if padpost:
        out+= padpost*'\n'

    return out

# ---------------------------------------------------------------------

def commentize( x, fullwid=76, indent=0, padpre=0, padpost=0,
                REP_TIL=True):
    '''Take a string and make it into a comment; indent uniformly, if
necessary.  Having '||' in a string (surrounded by whitespace) will
translate to starting a new line.

Inputs
------

    x : a string that is the cmd; should arranged into multiple lines
        (for long commands). Don't need/shouldn't have EOL chars.

    fullwid : can be any number of width; default is 76, since ' \'
        gets added on to most lines.

    indent : number of spaces to prepend to each line, if desired

    padpre : number of empty lines to affix beforehand

    padpost : number of empty lines to affix after text

    REP_TIL : replace any tilde '~' with a space at the end (may be
        useful because the lines are stripped of surrounding white
        space to start)

Returns
-------

    string : output >=1 line string version of the original, but
        spaced to not overrun the fullwid line width.  Can be
        uniformly indented.  If the input x is only whitespace or
        empty, then a null string is returned.

    '''

    y = x.split()

    new = []
    line = indent*' ' + '#'
    lenstart = len(line)
    for word in y:
        if word == "||":
            new.append(line)
            line = indent*' ' + '#'
        elif len(line) + len(word) < fullwid:
            line+= ' ' + word
        else:
            new.append(line)
            line = indent*' ' + '#'
            line+= ' ' + word
    # and get the last line, if there is any text still there beyond
    # just the starting stuff
    if len(line) > lenstart :
        new.append(line)

    out = '\n'.join(new)

    if padpre:
        out = padpre*'\n'+out
    if padpost:
        out+= padpost*'\n'

    if REP_TIL :
        out = out.replace('~', ' ')

    return out

# ---------------------------------------------------------------------

def echoize( x, efile='', indent=0, padpre=0, padpost=0,
             quote='''"''', REP_TIL=True):
    '''Take a string and make it into a series of echo statements that
will be sent into a text file; indent uniformly, if necessary.  Each
line is stripped of white space to start, but the '~' character will
be replaced by a space at the end, by default.  The 

Inputs
------

    x : a string that is the cmd; should arranged into multiple lines
        (for long commands). Don't need/shouldn't have EOL chars.

    efile : redirect echo to a file; otherwise, just sent to screen

    indent : number of spaces to prepend to each line, if desired

    padpre : number of empty lines to affix beforehand

    padpost : number of empty lines to affix after text

    quote : select kind of quote to use for echo; default is ".

    REP_TIL : replace any tilde '~' with a space at the end (may be
        useful because the lines are stripped of surrounding white
        space to start)

Returns
-------

    string : output >=1 line string version of the original, but
        spaced to not overrun the fullwid line width.  Can be
        uniformly indented.  If the input x is only whitespace or
        empty, then a null string is returned.

    '''

    multix = x.split('\n')
    N   = len(multix)
    new = []

    # set variable to contain output text file name
    if efile :
        new.append( '# text for output section in html'  )
        new.append( 'set otxt = {}'.format(efile) )

    for i in range(N):
        line = multix[i]
        ll = line.strip()
        y = indent * ' '
        y+= '''echo {}'''.format(quote) + ll + '''{}'''.format(quote)
        if REP_TIL:
            y = y.replace('~', ' ')
        if efile :
            # choose how to redirect each line
            red = '> ${otxt}' if ( i == 0 ) else '>> ${otxt}'
            y+= '''   {}'''.format(red)
        new.append(y)
        

    out = '\n'.join(new)

    if padpre:
        out = padpre*'\n'+out
    if padpost:
        out+= padpost*'\n'

    return out

# ======================================================================
# ======================================================================
# ===================== specifics for the dsets ========================
# ======================================================================
# ======================================================================

def make_apqc_top_vars(ssdict, fulllist):
    '''Count how many variables for QC imaging exist in the list searched
    for by gen_ss_review.py.  Build a tcsh-variable setting string of
    them.

    '''

    Nap = len(ssdict)

    if Nap:
        print('++ Found {} files for QCing.'.format(Nap))
    else:
        print('*+ Warning! Found *0* files for QCing???')
        sys.exit(0)

    out = ''
    for x in fulllist:
        if ssdict.__contains__(x):
            out+= 'set {} = {}\n'.format(x, ssdict[x])
    out = commandize( out, cmdindent=0, 
                      ALIGNASSIGN=True, ALLEOL=False,
                      padpre=1, padpost=2 )

    return out

# ----------------------------------------------------------------------

def make_apqc_dirs():
    '''Commands to make the QC/ and subdirs for images, etc. These are
fixed names, basically.  Should be run near start of prog.

    '''

    comm  = ''' pretty self explanatory'''

    # a little fun with curly brackets and Python's s.format()
    pre = '''
    set odir_qc = {}_${{subj}}
    set odir_img = ${{odir_qc}}/{}
    set odir_img = ${{odir_qc}}/{}
    set odir_info = ${{odir_qc}}/{}
    '''.format( qcbase, dir_img, dir_img, dir_info )

    cmd = '''
    \\mkdir -p ${odir_img}
    \\mkdir -p ${odir_img}
    \\mkdir -p ${odir_info}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd  = commandize( cmd, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False,
                       padpost=2 )

    lout = [comm, pre, cmd]
    return '\n\n'.join(lout)

# ========================== other top vars ==============================

# need to *find* the template...
# ['template']
def apqc_find_template( ):

    comm  = '''Find the template'''

    pre = '''
    set btemp = `basename ${template}`
    '''

    pre2 = '''# try to locate the template
set templ_path = `@FindAfniDsetPath ${template}`

if ( ${#templ_path} ) then
    set templ_vol = "${templ_path}/${btemp}"
    echo "*+ Found ${templ_vol}"
else
    echo "** ERROR: Cannot find template, even though one was specified."
    echo "   Please place the template in a findable spot, and try again."
    exit 1
endif

'''

    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )

    lout = [pre, pre2]
    return '\n\n'.join(lout)

# ========================== 1D files/plots ==============================

# ['motion_dset', 'nt_orig']
def apqc_mot_VR6( obase, qcb, qci, run_style, jpgsize ):

    opref = '_'.join([obase, qcb, qci]) # full name

    comm  = ''' review plots: 3dvolreg motion regressors'''

    pre = '''
    set jpgsize = {} 
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    @ imax = ${{nt_orig}} - 1
    set ssrev_ln = `grep "num TRs per run" ${{ss_review_dset}} | grep -v "("`
    set pats = "${{ssrev_ln[6-]}}"
    '''.format(jpgsize, opref)
    
    STR_plot_title = '''Estimated motion parameters (volreg)'''
    STR_json_text  = '''6 volume registration motion parameters (in ${motion_dset})'''

    if run_style == 'basic' :
        cmd = '''
        1dplot                                                     
        -sepscl 
        -volreg 
        -xlabel   "vol"
        -title    "{}"
        -jpgs     ${{jpgsize}} "${{odir_img}}/${{opref}}" 
        "${{motion_dset}}" 
        '''.format( STR_plot_title )

    elif run_style == 'pythonic' :
        cmd = '''
        1dplot.py                                                     
        -sepscl 
        -boxplot_on    
        -patches ${{pats}}
        -reverse_order 
        -infiles  "${{motion_dset}}"
        -ylabels   VOLREG
        -xlabel   "vol index"
        -title    "{}"
        -prefix   "${{odir_img}}/${{opref}}.jpg" 
        '''.format( STR_plot_title )

    # text shown above image in the final HTML
    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: 1D
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text        :: "{}"
    EOF
    '''.format( qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1],
                STR_json_text )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm  = commentize( comm )
    pre   = commandize( pre, cmdindent=0, 
                        ALIGNASSIGN=True, ALLEOL=False )
    cmd   = commandize( cmd )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2  )

    lout  = [comm, pre, cmd, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)

# ----------------------------------------------------------------------

# **NB**: it is likely that any changes in this function should mirror
# those of apqc_mot_enorm() and apqc_mot_enormoutlr

# ['outlier_dset', 'nt_orig'], also use 'censor_dset' and 'out_limit'
def apqc_mot_outlr( obase, qcb, qci, run_style, jpgsize,
                    has_cen_dset=False,
                    has_lim=False ):

    # [PT] A note about the multiplicative factor in ${ytop}:
    # visually, a factor of 3 seems to be a good balance for this
    # scaling.  The plot is clear, and sub-threshold motion seems
    # "small" quickly: with a smaller factor like 2, even some
    # subthreshold motion appears "large"; larger factors waste space.

    opref = '_'.join([obase, qcb, qci]) # full name

    if run_style == 'basic' :
        cen_color = 'green'
    elif run_style == 'pythonic' :
        cen_color = 'red'

    STR_CEN_pre    = '''set cstr = "(no censoring applied)"'''
    STR_plot_title = 'Outlier frac (black)'
    STR_json_text  = 'Volumetric fraction of outliers'
    STR_json_subt  = ''
    if has_cen_dset : 
        STR_json_subt+= '''censored vols (${Pcstr}%): ${cstr}'''
        STR_CEN_pre = '''set cstr = `1d_tool.py -show_trs_censored encoded -infile ${censor_dset}`
        set Ncstr = `1d_tool.py -verb 0 -show_censor_count -infile ${censor_dset}`
        set Pcstr = `echo "scale=0; ${Ncstr} * 100 / ${nt_orig}" | bc`'''
        if has_lim : 
            STR_plot_title+= ''', with limit (cyan)'''
            STR_json_text+=  ''', with limit'''
            STR_CEN_pre+= '''\n set ytop = `echo "3 * ${out_limit}" | bc`'''
        STR_plot_title+= ''' and combined censoring ({})'''.format( cen_color )
        STR_json_text+=  ''' and combined censoring'''

    comm  = ''' review plots (colored TRs are censored); outliers with 
    fraction limit'''

    pre = '''
    set jpgsize = {} 
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    @ imax = ${{nt_orig}} - 1
    set ssrev_ln = `grep "num TRs per run" ${{ss_review_dset}} | grep -v "("`
    set pats = "${{ssrev_ln[6-]}}"
    {}
    '''.format(jpgsize, opref, STR_CEN_pre)

    if run_style == 'basic' :

        # extra uvars may or may not be used
        # [PT: Dec 23, 2018] also include yaxis scaling by censor
        # levels, if given
        STR_CEN_cmd = ''
        STR_LIM_cmd = ''
        if has_cen_dset : 
            STR_CEN_cmd+= '''-censor_RGB green 
                             -censor   ${censor_dset}'''
            # think one only has a censor limit if one has a censor file??
            if has_lim : 
                STR_LIM_cmd+= '''"1D: ${nt_orig}@${out_limit}"'''
                STR_CEN_cmd+= '''\n -yaxis    0:${ytop}:6:2'''

        cmd = '''
        1dplot
        -one 
        {}
        -jpgs     ${{jpgsize}} "${{odir_img}}/${{opref}}"
        -aspect   2
        -xlabel   "vol"
        -title    "{}"
        ${{outlier_dset}}
        {}
        '''.format( STR_CEN_cmd, STR_plot_title, STR_LIM_cmd )

    elif run_style == 'pythonic' :

        # extra uvars may or may not be used
        STR_CEN_cmd  = ''
        STR_LIM_cmd  = ''
        if has_cen_dset : 
            STR_CEN_cmd+= '''-censor_files ${censor_dset}'''
            # think one only has a censor limit if one has a censor file??
            if has_lim : 
                STR_LIM_cmd+= '''-censor_hline ${out_limit}'''
                STR_CEN_cmd+= '''\n -yaxis    0:${ytop}'''

        cmd = '''
        1dplot.py                                                     
        -boxplot_on    
        -patches ${{pats}}
        -reverse_order 
        -infiles  "${{outlier_dset}}"
        -ylabels   "frac"
        {}
        {}
        -xlabel   "vol index"
        -title    "{}"
        -prefix   "${{odir_img}}/${{opref}}.jpg" 
        '''.format( STR_CEN_cmd, STR_LIM_cmd, STR_plot_title)

    # text shown above image in the final HTML; same for basic and
    # pythonic, b/c just the format strings hold differences now
    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: 1D
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text        :: "{}"
    subtext     :: "{}"
    EOF
    '''.format( qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1], 
                STR_json_text, STR_json_subt )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False)
    cmd  = commandize( cmd )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2  )

    lout = [comm, pre, cmd, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)

# ----------------------------------------------------------------------

# **NB**: it is likely that any changes in this function should mirror
# those of apqc_mot_outlr and apqc_mot_enormoutlr

# ['censor_dset', 'enorm_dset', 'mot_limit', 'nt_orig']
def apqc_mot_enorm( obase, qcb, qci, run_style, jpgsize, 
                    has_cen_dset=False,
                    has_lim=False ):

    opref = '_'.join([obase, qcb, qci]) # full name

    if run_style == 'basic' :
        cen_color = 'green'
    elif run_style == 'pythonic' :
        cen_color = 'red'

    STR_CEN_pre    = '''set cstr = "(no censoring applied)"'''
    STR_plot_title = 'Mot enorm (black)'
    STR_json_text  = 'Motion Euclidean norm (enorm)'
    STR_json_text2  = ''             # stuff to go on second line
    STR_json_subt  = ''
    if has_cen_dset : 
        STR_json_subt+= '''censored vols (${Pcstr}%): ${cstr}'''
        STR_CEN_pre = '''set cstr = `1d_tool.py -show_trs_censored encoded -infile ${censor_dset}`
        set Ncstr = `1d_tool.py -verb 0 -show_censor_count -infile ${censor_dset}`
        set Pcstr = `echo "scale=0; ${Ncstr} * 100 / ${nt_orig}" | bc`'''
        if has_lim : 
            STR_plot_title+= ''', with limit (cyan)'''
            STR_json_text2+=  '''with limit'''
            STR_CEN_pre+= '''\n set ytop = `echo "3 * ${mot_limit}" | bc`'''
        STR_plot_title+= ''' and combined censoring ({})'''.format( cen_color )
        STR_json_text2+= ''' and combined censoring'''

    if STR_json_text2:
        STR_json_text+= ' ,, ' + STR_json_text2

    comm  = ''' review plots (colored TRs are censored); outliers with 
    enorm motion limit'''

    pre = '''
    set jpgsize = {} 
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    @ imax = ${{nt_orig}} - 1
    set ssrev_ln = `grep "num TRs per run" ${{ss_review_dset}} | grep -v "("`
    set pats = "${{ssrev_ln[6-]}}"
    {}
    '''.format( jpgsize, opref, STR_CEN_pre )

    if run_style == 'basic' :

        # extra uvars may or may not be used
        STR_CEN_cmd  = ''
        STR_LIM_cmd  = ''
        if has_cen_dset : 
            STR_CEN_cmd+= '''-censor_RGB green 
                             -censor   ${censor_dset}'''
            # think one only has a censor limit if one has a censor file??
            if has_lim : 
                STR_LIM_cmd+= '''"1D: ${nt_orig}@${mot_limit}"'''
                STR_CEN_cmd+= '''\n -yaxis    0:${ytop}:6:2'''

        cmd = '''
        1dplot 
        -one 
        {}
        -jpgs     ${{jpgsize}} "${{odir_img}}/${{opref}}"
        -aspect   2
        -xlabel   "vol"
        -title    "{}"
        ${{enorm_dset}}
        {}
        '''.format( STR_CEN_cmd, STR_plot_title, STR_LIM_cmd )

    elif run_style == 'pythonic' :

        # extra uvars may or may not be used
        STR_CEN_cmd = ''
        STR_LIM_cmd = ''
        if has_cen_dset : 
            STR_CEN_cmd+= '''-censor_files ${censor_dset}'''
            # think one only has a censor limit if one has a censor file??
            if has_lim : 
                STR_LIM_cmd+= '''-censor_hline ${mot_limit}'''
                STR_CEN_cmd+= '''\n -yaxis    0:${ytop}'''

        cmd = '''
        1dplot.py                                                     
        -boxplot_on    
        -patches ${{pats}}
        -infiles  "${{enorm_dset}}"
        -ylabels   "enorm (~mm)"
        {}
        {}
        -xlabel   "vol index"
        -title    "{}"
        -prefix   "${{odir_img}}/${{opref}}.jpg" 
        '''.format( STR_CEN_cmd, STR_LIM_cmd, STR_plot_title)

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: 1D
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text        :: {}
    subtext     :: "{}"
    EOF
    '''.format( qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1], 
                STR_json_text, STR_json_subt )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd  = commandize( cmd, REP_TIL=False )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2  )

    lout = [comm, pre, cmd, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)

# ---------------------------------------------------------------------
# [PT: Jan 13, 2019] combo img when both motion and outliers are calc'ed

# ['outlier_dset', 'out_limit', 'enorm_dset', 'mot_limit',
# 'censor_dset', 'nt_orig']
def apqc_mot_enormoutlr( obase, qcb, qci, run_style, jpgsize, 
                         has_cen_dset=False,
                         has_lim_mot=False,
                         has_lim_out=False ):

    opref = '_'.join([obase, qcb, qci]) # full name

    if run_style == 'basic' :
        cen_color = 'green'
    elif run_style == 'pythonic' :
        cen_color = 'red'

    # Strings for titles, text and subtext, as well as other calcs
    STR_CEN_pre    = '''set cstr = "(no censoring applied)"'''
    STR_plot_title = 'Mot enorm and outlier frac (black)'
    STR_json_text  = 'Motion Euclidean norm (enorm) and outlier fraction'
    STR_json_text2  = ''             # stuff to go on second line
    STR_json_subt  = ''
    if has_cen_dset : 
        STR_json_subt+= '''censored vols (${Pcstr}%): ${cstr}'''
        STR_CEN_pre = '''set cstr = `1d_tool.py -show_trs_censored encoded -infile ${censor_dset}`
        set Ncstr = `1d_tool.py -verb 0 -show_censor_count -infile ${censor_dset}`
        set Pcstr = `echo "scale=0; ${Ncstr} * 100 / ${nt_orig}" | bc`'''
        if has_lim_mot or has_lim_out : 
            STR_plot_title+= ''', with limit (cyan)'''
            STR_json_text2+=  '''with limit'''
            if has_lim_mot :
                STR_CEN_pre+= '''\n set ytop_mot = `echo "3 * ${mot_limit}" | bc`'''
            if has_lim_out :
                STR_CEN_pre+= '''\n set ytop_out = `echo "3 * ${out_limit}" | bc`'''
        STR_plot_title+= ''' and combined censoring ({})'''.format( cen_color )
        STR_json_text2+= ''' and combined censoring'''

    if STR_json_text2:
        STR_json_text+= ' ,, ' + STR_json_text2

    comm  = ''' review plots (colored TRs are censored); outliers with 
    enorm motion limit'''

    pre = '''
    set jpgsize = {} 
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    @ imax = ${{nt_orig}} - 1
    set ssrev_ln = `grep "num TRs per run" ${{ss_review_dset}} | grep -v "("`
    set pats = "${{ssrev_ln[6-]}}"
    {}
    '''.format( jpgsize, opref, STR_CEN_pre )
    
    # A truism for this plot, at the moment
    if run_style == 'pythonic' :

        # stuff for 1dplot.py command
        STR_CEN_cmd = ''
        STR_LIM_cmd = ''
        if has_cen_dset : 
            STR_CEN_cmd+= '''-censor_files ${censor_dset}'''
            # think one only has a censor limit if one has a censor file??
            if has_lim_mot or has_lim_out : 
                STR_LIM_cmd+= '''-censor_hline '''
                STR_CEN_cmd+= '''\n -yaxis '''
                if has_lim_mot :
                    STR_LIM_cmd+= ''' ${mot_limit}'''
                    STR_CEN_cmd+= ''' 0:${ytop_mot} '''
                if has_lim_out :
                    STR_LIM_cmd+= ''' ${out_limit}'''
                    STR_CEN_cmd+= ''' 0:${ytop_out} '''

        cmd = '''
        1dplot.py                                                     
        -boxplot_on    
        -patches ${{pats}}
        -colors black
        -infiles  "${{enorm_dset}}" "${{outlier_dset}}"
        -ylabels   "enorm (~mm)" "outlier frac"
        {}
        {}
        -xlabel   "vol index"
        -title    "{}"
        -prefix   "${{odir_img}}/${{opref}}.jpg" 
        '''.format( STR_CEN_cmd, STR_LIM_cmd, STR_plot_title)

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: 1D
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text        :: {}
    subtext     :: "{}"
    EOF
    '''.format( qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1], 
                STR_json_text, STR_json_subt )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd  = commandize( cmd, REP_TIL=False )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2  )

    lout = [comm, pre, cmd, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)


# ---------------------------------------------------------------------
# [PT: Dec 23, 2018] add in viewing censor dset, if present

# !!! need to get stim file labels for each!

# ['xmat_stim']
def apqc_regr_stims( obase, qcb, qci, run_style, jpgsize, 
                     has_cen_dset=False ):

    opref = '_'.join([obase, qcb, qci]) # full name

    if run_style == 'basic' :
        cen_color = 'green'
    elif run_style == 'pythonic' :
        cen_color = 'red'

    # censoring, but no limit shown here
    STR_CEN_pre    = '''set cstr = "(no censoring applied)"'''
    STR_plot_title = 'Regressors of interest in the X-matrix'
    STR_json_text  = 'regressors of interest (per stim, in ${xmat_stim})'
    STR_json_subt  = ''
    if has_cen_dset : 
        STR_plot_title+= ''' and combined censoring ({})'''.format( cen_color )
        STR_json_text+=  ''' and combined censoring'''
        STR_json_subt+=  '''censored vols (${Pcstr}%): ${cstr}'''
        STR_CEN_pre = '''set cstr = `1d_tool.py -show_trs_censored encoded -infile ${censor_dset}`
        set Ncstr = `1d_tool.py -verb 0 -show_censor_count -infile ${censor_dset}`
        set Pcstr = `echo "scale=0; ${Ncstr} * 100 / ${nt_orig}" | bc`'''

    comm  = ''' view xmatrix (${xmat_stim}), made from (${xmat_uncensored})'''

    pre = '''
    set jpgsize = {} 
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    @ imax = ${{nt_orig}} - 1
    set ssrev_ln = `grep "num TRs per run" ${{ss_review_dset}} | grep -v "("`
    set pats = "${{ssrev_ln[6-]}}"
    '''.format(jpgsize, opref)

    if run_style == 'basic' :

        STR_CEN_cmd = ''
        if has_cen_dset : 
            STR_CEN_cmd+= '''-censor_RGB green 
                             -censor   ${censor_dset}'''

        cmd = '''
        1dplot 
        -sepscl 
        {}
        -jpgs     $jpgsize "${{odir_img}}/${{opref}}"
        -aspect   2
        -xlabel   "vol"
        -title    "{}"
        ${{xmat_stim}}
        '''.format( STR_CEN_cmd, STR_plot_title )

    elif run_style == 'pythonic' :

        STR_CEN_cmd = ''
        if has_cen_dset : 
            STR_CEN_cmd+= '''-censor_files ${censor_dset}'''

        cmd = '''
        1dplot.py 
        -sepscl 
        -boxplot_on
        -patches ${{pats}}
        -reverse_order 
        -infiles  ${{xmat_stim}}
        -xlabel   "vol"
        {}
        -title    "{}"
        -prefix   "${{odir_img}}/${{opref}}.jpg"
        '''.format( STR_CEN_cmd, STR_plot_title )

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: 1D
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text        :: "{}"
    subtext     :: "{}"
    EOF
    '''.format( qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1], 
                STR_json_text, STR_json_subt )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd  = commandize( cmd )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2  )

    lout = [comm, pre, cmd, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)

# ------------------------------------------------------------------

# ['sum_ideal']
def apqc_regr_ideal( obase, qcb, qci, run_style, jpgsize, 
                     has_cen_dset=False ):

    opref = '_'.join([obase, qcb, qci]) # full name

    if run_style == 'basic' :
        cen_color = 'green'
    elif run_style == 'pythonic' :
        cen_color = 'red'

    # censoring, but no limit shown here
    STR_CEN_pre    = '''set cstr = "(no censoring applied)"'''
    STR_plot_title = 'Sum of regressors of interest in the X-matrix'
    STR_json_text  = 'sum of regressors of interest (in ${sum_ideal})'
    STR_json_subt  = ''
    if has_cen_dset : 
        STR_plot_title+= ''' and combined censoring ({})'''.format( cen_color )
        STR_json_text+=  ''' and combined censoring'''
        STR_json_subt+=  '''censored vols (${Pcstr}%): ${cstr}'''
        STR_CEN_pre = '''set cstr = `1d_tool.py -show_trs_censored encoded -infile ${censor_dset}`
        set Ncstr = `1d_tool.py -verb 0 -show_censor_count -infile ${censor_dset}`
        set Pcstr = `echo "scale=0; ${Ncstr} * 100 / ${nt_orig}" | bc`'''

    comm  = ''' view xmatrix'''

    pre = '''
    set jpgsize = {} 
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    @ imax = ${{nt_orig}} - 1
    set ssrev_ln = `grep "num TRs per run" ${{ss_review_dset}} | grep -v "("`
    set pats = "${{ssrev_ln[6-]}}"
    '''.format(jpgsize, opref)

    if run_style == 'basic' :

        # extra uvars may or may not be used
        STR_CEN_cmd  = ''
        if has_cen_dset : 
            STR_CEN_cmd+= '''-censor_RGB green 
                             -censor   ${censor_dset}'''

        cmd = '''
        1dplot 
        -sepscl
        {}
        -jpgs     $jpgsize "${{odir_img}}/${{opref}}"
        -aspect   2
        -xlabel   "vol"
        -title    "{}"
        ${{sum_ideal}}
        '''.format( STR_CEN_cmd, STR_plot_title )

    elif run_style == 'pythonic' :

        # extra uvars may or may not be used; censoring, but no limit
        STR_CEN_cmd = ''
        if has_cen_dset : 
            STR_CEN_cmd+= '''-censor_files ${censor_dset}'''

        cmd = '''
        1dplot.py 
        -boxplot_on
        -patches ${{pats}}
        -colors black
        -sepscl 
        -boxplot_on
        -infiles  ${{sum_ideal}}
        -xlabel   "vol"
        {}
        -title    "{}"
        -prefix   "${{odir_img}}/${{opref}}.jpg"
        '''.format( STR_CEN_cmd, STR_plot_title)

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: 1D
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text        :: "{}"
    subtext     :: "{}"
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1], 
               STR_json_text, STR_json_subt )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd  = commandize( cmd )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2  )

    lout = [comm, pre, cmd, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)


# ========================== images ================================

# ----------------------------------------------------------------------

# ['vr_base'] OR ['anat_orig']
def apqc_vorig_all( obase, qcb, qci, olay_posonly=True, ulay_name='' ):
    # Here, qci has additional roles of a string label, because we use
    # this same function to plot all ORIG vols (EPI or anat, at the
    # moment)

    opref = '_'.join([obase, qcb, qci]) # full name

    perc_olay_top = 98                    # %ile for top of pbar for olay

    # what will minval of pbar be? 0, or -max?
    if olay_posonly :
        olay_minval_str = "-pbar_posonly"
        pbar_min        = "0"

    comm  = '''Check the quality of acquired {} in orig space (ulay)
            {} %ile topval for pbar'''.format( qci, perc_olay_top )

    # minor tweaks/formatting/expanding
    epi_comm = ''
    if qci == "EPI":
        epi_comm =  ' (volreg base)'
    qci_comm = qci
    if qci == "anat":
        qci_comm = 'Anatomical'

    STR_json_text = '''"{} in original space{}"'''.format( qci_comm, epi_comm )
    STR_json_text+= ''' ,, '''   # separator for 2-line text in JSON
    STR_json_text+= '''"ulay: ${{ulay_name}} ({})"'''.format( qci )

    pre = '''
    set opref = {0}
    set ulay = "${{{1}}}"
    set ulay_name = `3dinfo -prefix ${{{1}}}`
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.axi.json
    set tjson2  = _tmp2.txt
    set ojson2  = ${{odir_img}}/${{opref}}.sag.json
    set tpbarjson  = _tmppbar.txt
    set opbarjson  = ${{odir_img}}/${{opref}}.pbar.json
    '''.format( opref, ulay_name )

    # get min/max for informational purposes
    cmd1 = '''
    set minmax = `3dBrickStat 
    -slow 
    -min -max
    ${{ulay}}`
    '''.format( perc_olay_top )

    # top value for colorbar of olay, from %ile in VOL; should just be
    # single brick, so don't need a selector
    cmd2 = '''
    set pp = `3dBrickStat 
    -slow 
    -percentile {0} 1 {0}
    ${{ulay}}`
    '''.format( perc_olay_top )

    cmd3 = '''
    set olay_topval = ${{pp[2]}}
    set olay_botval = {}
    '''.format( pbar_min )

    cmd4 = '''
    @chauffeur_afni
    -ulay    ${{ulay}}
    -olay    ${{ulay}}
    -ulay_range_nz 0 ${{olay_topval}}
    -func_range ${{olay_topval}}
    -box_focus_slices AMASK_FOCUS_ULAY
    -cbar gray_scale 
    {}
    -pbar_saveim "${{odir_img}}/${{opref}}.pbar.jpg"
    -prefix      "${{odir_img}}/${{opref}}"
    -save_ftype JPEG
    -blowup 4
    -opacity 9  
    -montx 7 -monty 1  
    -set_xhairs OFF 
    -label_mode 1 -label_size 3  
    -do_clean
    '''.format( olay_minval_str )

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: VOL
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text        :: {}
    EOF
    '''.format( qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1],
                STR_json_text )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    jsontxt2 = '''
    cat << EOF >! ${{tjson2}}
    itemtype    :: VOL
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt2_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson2}
    -prefix ${ojson2}
    '''


    # Here, we cheat a bit by calling the volume a 'ulay'.  The reason
    # we do this is that it seems more compatible with general AFNI
    # viewing of having a grayscale ulay and a colored olay.
    pbarjsontxt = '''
    cat << EOF >! ${{tpbarjson}}
    pbar_bot :: ${{olay_botval}}
    pbar_top :: ${{olay_topval}}
    pbar_reason :: {}{}
    pbar_vol :: " ulay"
    pbar_comm :: "range: ${{minmax[1]}}, ${{minmax[2]}}"
    EOF
    '''.format( perc_olay_top, '''%ile in vol''' )

    pbarjsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tpbarjson}
    -prefix ${opbarjson}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd1  = commandize( cmd1 )
    cmd2  = commandize( cmd2 )
    cmd3  = commandize( cmd3, cmdindent=0, 
                        ALIGNASSIGN=True, ALLEOL=False )
    cmd4  = commandize( cmd4 )

    # NB: for commandizing the *jsontxt commands, one NEEDS
    # 'cmdindent=0', bc 'EOF' cannot be indented to be detected
    pbarjsontxt = commandize( pbarjsontxt, cmdindent=0, ALLEOL=False )
    pbarjsontxt_cmd  = commandize( pbarjsontxt_cmd )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )
    jsontxt2 = commandize( jsontxt2, cmdindent=0, ALLEOL=False )
    jsontxt2_cmd  = commandize( jsontxt2_cmd, padpost=2 )

    lout = [comm, pre, cmd1, cmd2, cmd3, cmd4, 
            pbarjsontxt, pbarjsontxt_cmd, jsontxt, jsontxt_cmd, 
            jsontxt2, jsontxt2_cmd]
    return '\n\n'.join(lout)

# ----------------------------------------------------------------------


# ['final_anat', 'final_epi_dset']
def apqc_ve2a_epi2anat( obase, qcb, qci, focusbox ):

    opref = '_'.join([obase, qcb, qci]) # full name

    comm  = '''Compare the quality of alignment between the anatomical 
    (ulay) and edge-ified EPI (olay): || look at gross alignment || 
    follow ventricles and gyral patterns'''

    pre = '''
    set opref = {}
    set focus_box = {}
    set ulay_name = `3dinfo -prefix ${{final_anat}}`
    set olay_name = `3dinfo -prefix ${{final_epi_dset}}`
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.axi.json
    set tjson2  = _tmp2.txt
    set ojson2  = ${{odir_img}}/${{opref}}.sag.json
    '''.format( opref, focusbox )

    cmd = '''
    @djunct_edgy_align_check
    -ulay    ${final_anat}
    -box_focus_slices ${focus_box}
    -olay    ${final_epi_dset}
    -prefix  ${odir_img}/${opref}

    '''

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: VOL
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text  ::  "ulay: ${{ulay_name}} (anat)",, "olay: ${{olay_name}} (EPI edges)"
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    jsontxt2 = '''
    cat << EOF >! ${{tjson2}}
    itemtype    :: VOL
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt2_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson2}
    -prefix ${ojson2}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd  = commandize( cmd )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )
    jsontxt2 = commandize( jsontxt2, cmdindent=0, ALLEOL=False )
    jsontxt2_cmd  = commandize( jsontxt2_cmd, padpost=2 )

    lout = [comm, pre, cmd, jsontxt, jsontxt_cmd, jsontxt2, jsontxt2_cmd]
    return '\n\n'.join(lout)

# ----------------------------------------------------------------------

# ['final_anat', 'template']
def apqc_va2t_anat2temp( obase, qcb, qci, focusbox ):

    opref = '_'.join([obase, qcb, qci]) # full name

    comm  = '''Compare the quality of alignment between the template 
    (ulay) and edge-ified anatomical (olay): || look at gross alignment || 
    follow ventricles and gyral patterns'''

    pre = '''
    set opref = {}
    set focus_box = {}
    set ulay_name = `3dinfo -prefix ${{templ_vol}}`
    set olay_name = `3dinfo -prefix ${{final_anat}}`
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.axi.json
    set tjson2  = _tmp2.txt
    set ojson2  = ${{odir_img}}/${{opref}}.sag.json
    '''.format( opref, focusbox )

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: VOL
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text  ::  "ulay: ${{ulay_name}} (template)",, "olay: ${{olay_name}} (anat edges)"
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    jsontxt2 = '''
    cat << EOF >! ${{tjson2}}
    itemtype    :: VOL
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt2_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson2}
    -prefix ${ojson2}
    '''

    # !!!! ? need '[0]' selector here because (multibrick) SSW reference
    # templates could be reference template 
    cmd = '''
    @djunct_edgy_align_check
    -ulay    ${templ_vol}
    -box_focus_slices ${focus_box}
    -olay    ${final_anat}
    -prefix  ${odir_img}/${opref}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd  = commandize( cmd )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )
    jsontxt2 = commandize( jsontxt2, cmdindent=0, ALLEOL=False )
    jsontxt2_cmd  = commandize( jsontxt2_cmd, padpost=2 )

    lout = [comm, pre, cmd, jsontxt, jsontxt_cmd, jsontxt2, jsontxt2_cmd]
    return '\n\n'.join(lout)


# ['stats_dset', 'mask_dset', 'final_anat']
# ['template'] # secondary consideration
def apqc_vstat_fstat( obase, qcb, qci, focusbox, iolay, ithr, 
                      olay_posonly=True ):

    opref = '_'.join([obase, qcb, qci]) # full name

    perc_thr_thr  = 90                    # %ile for thresholding thr vol
    perc_olay_top = 99                    # %ile for top of pbar for olay

    # what will minval of pbar be? 0, or -max?
    if olay_posonly :
        olay_minval_str = "-pbar_posonly"
        pbar_min        = "0"
    else:
        olay_minval_str = "-pass"
        pbar_min        = "-${olay_topval}" # $olay_topval is defined below

    comm  = '''peruse statistical results: 
    {} %ile threshold of thr vol [{}]
    {} %ile topval for olay vol [{}] for pbar'''.format( perc_thr_thr,
                                                         ithr,
                                                         perc_olay_top,
                                                         iolay )

    # NB: below, note the '.axi.json', because of how @chauffeur_afni
    # appends slice plane in the name of each output image
    pre = '''
    set opref = {}
    set focus_box = {}
    set ulay_name = `3dinfo -prefix ${{final_anat}}`
    set olay_name = `3dinfo -prefix ${{stats_dset}}`
    set olaybrick = {}
    set olaylabel = `3dinfo -label ${{stats_dset}}"[${{olaybrick}}]"`
    set thrbrick = {}
    set thrlabel = `3dinfo -label ${{stats_dset}}"[${{thrbrick}}]"`
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.axi.json
    set tjson2  = _tmp2.txt
    set ojson2  = ${{odir_img}}/${{opref}}.sag.json
    set tpbarjson  = _tmppbar.txt
    set opbarjson  = ${{odir_img}}/${{opref}}.pbar.json
    '''.format( opref, focusbox, iolay, ithr )

    # threshold for stat dset, from %ile in mask
    cmd0 = '''
    set tt = `3dBrickStat 
    -slow 
    -percentile {0} 1 {0}
    -mask "${{mask_dset}}" 
    ${{stats_dset}}"[${{thrbrick}}]"`
    '''.format( perc_thr_thr )

    cmd1 = '''
    set thr_thresh = ${tt[2]}
    '''

    # top value for colorbar of olay, from %ile in mask
    cmd2 = '''
    set pp = `3dBrickStat 
    -slow 
    -percentile {0} 1 {0}
    -mask "${{mask_dset}}" 
    ${{stats_dset}}"[${{olaybrick}}]"`
    '''.format( perc_olay_top )

    cmd3 = '''
    set olay_topval = ${{pp[2]}}
    set olay_botval = {}
    '''.format( pbar_min )

    cmd4 = '''
    @chauffeur_afni    
    -ulay  ${{final_anat}}
    -box_focus_slices ${{focus_box}}
    -olay  ${{stats_dset}}  
    -cbar Plasma 
    {}
    -ulay_range 0% 120%  
    -func_range ${{olay_topval}}
    -thr_olay ${{thr_thresh}}    
    -olay_alpha Yes
    -olay_boxed Yes
    -set_subbricks -1 ${{olaybrick}} ${{thrbrick}}
    -opacity 9  
    -pbar_saveim   "${{odir_img}}/${{opref}}.pbar.jpg"
    -prefix        "${{odir_img}}/${{opref}}"
    -save_ftype JPEG
    -montx 7 -monty 1  
    -set_xhairs OFF 
    -label_mode 1 -label_size 3  
    -do_clean
    '''.format( olay_minval_str )

    # As default, use :: and ,, as major and minor delimiters,
    # respectively, because those should be useful in general.  
    # NB: because we want the single apostrophe to appear as a text
    # character, we have to wrap this with the double quotes
    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: VOL
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text  ::  "olay: ${{olay_name}} (stat '${{olaylabel}}')",, "thr : ${{olay_name}} (stat '${{thrlabel}}')"
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    jsontxt2 = '''
    cat << EOF >! ${{tjson2}}
    itemtype    :: VOL
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt2_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson2}
    -prefix ${ojson2}
    '''

    pbarjsontxt = '''
    cat << EOF >! ${{tpbarjson}}
    pbar_bot :: ${{olay_botval}}
    pbar_top :: ${{olay_topval}}
    pbar_reason :: {}{}
    vthr :: ${{thr_thresh}}
    vthr_reason :: {}{}
    EOF
    '''.format( perc_olay_top, '''%ile in mask''', 
                perc_thr_thr,  '''%ile in mask''' )

    pbarjsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tpbarjson}
    -prefix ${opbarjson}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd0  = commandize( cmd0 )
    cmd1  = commandize( cmd1 )
    cmd2  = commandize( cmd2 )
    cmd3  = commandize( cmd3, cmdindent=0, 
                        ALIGNASSIGN=True, ALLEOL=False )
    cmd4  = commandize( cmd4 )

    # NB: for commandizing the *jsontxt commands, one NEEDS
    # 'cmdindent=0', bc 'EOF' cannot be indented to be detected
    pbarjsontxt = commandize( pbarjsontxt, cmdindent=0, ALLEOL=False )
    pbarjsontxt_cmd  = commandize( pbarjsontxt_cmd )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )
    jsontxt2 = commandize( jsontxt2, cmdindent=0, ALLEOL=False )
    jsontxt2_cmd  = commandize( jsontxt2_cmd, padpost=2 )

    lout = [comm, pre, cmd0, cmd1, cmd2, cmd3, cmd4, 
            pbarjsontxt, pbarjsontxt_cmd, jsontxt, jsontxt_cmd, 
            jsontxt2, jsontxt2_cmd]
    return '\n\n'.join(lout)


# ========================== dat/txt ================================


# summary quantities from 1d_tool.py degree-o-freedom check
# ['xmat_regress']
def apqc_regr_df( obase, qcb, qci ):

    opref = '_'.join([obase, qcb, qci]) # full name

    comm  = '''df check for processing'''

    pre = '''
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    '''.format( opref )

    cmd0 = '''
    1d_tool.py -show_df_info -infile ${xmat_regress}
    > ${odir_img}/${opref}.dat
    '''

    cmd1 = '''
    echo "++ Check summary of degrees of freedom in: ${odir_img}/${opref}.dat"
    '''
    
    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: DAT
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text  ::  "Summary of degrees of freedom (DF) usage from processing"
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm  = commentize( comm )
    pre   = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd0  = commandize( cmd0 )
    cmd1  = commandize( cmd1, ALLEOL=False )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )

    lout = [comm, pre, cmd0, cmd1, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)

# ---------------------------------------------------------------------

# summary quantities from @ss_review_basic dumped to text file
# 1
def apqc_qsumm_ssrev( obase, qcb, qci ):

    opref = '_'.join([obase, qcb, qci]) # full name

    comm  = '''summary quantities from processing'''

    pre = '''
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    '''.format( opref )

    cmd0 = '''
    cat out.ss_review.${subj}.txt
    > ${odir_img}/${opref}.dat
    '''

    cmd1 = '''
    echo "++ Check basic summary quants from proc in: ${odir_img}/${opref}.dat"
    '''
    
    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: DAT
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text  ::  "basic summary quantities from processing"
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm  = commentize( comm )
    pre   = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd0  = commandize( cmd0 )
    cmd1  = commandize( cmd1, ALLEOL=False )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )

    lout = [comm, pre, cmd0, cmd1, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)


# ========================== warn/txt ================================

# Text warning, goes to dir_img output
# ['xmat_regress']
def apqc_warns_xmat( obase, qcb, qci ):

    opref = '_'.join([obase, qcb, qci]) # full name

    comm  = '''review: check for correlation matrix warnings'''

    pre = '''
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    '''.format( opref )

    cmd0 = '''
    1d_tool.py 
    -show_cormat_warnings 
    -infile ${xmat_regress}
    > ${odir_img}/${opref}.dat
    '''

    cmd1 = '''
    echo "++ Check for corr matrix warnings in: ${odir_img}/${opref}.dat"
    '''

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: WARN
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text  ::  "regression matrix correlation warnings"
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm  = commentize( comm )
    pre   = commandize( pre, cmdindent=0, 
                        ALIGNASSIGN=True, ALLEOL=False )
    cmd0  = commandize( cmd0 )
    cmd1  = commandize( cmd1, ALLEOL=False )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )

    lout = [comm, pre, cmd0, cmd1, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)

# ----------------------------------------------------------------------

# Text warning, goes to dir_img output
# ['pre_ss_warn_dset']
def apqc_warns_press( obase, qcb, qci ):

    opref = '_'.join([obase, qcb, qci]) # full name

    comm  = '''review: check for pre-steady state warnings'''

    pre = '''
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    '''.format( opref )

    cmd = '''
    if ( -f ${pre_ss_warn_dset} && ! -z ${pre_ss_warn_dset} ) then
    ~~~~cat ${pre_ss_warn_dset} > ${odir_img}/${opref}.dat
    else
    ~~~~echo " none "  > ${odir_img}/${opref}.dat
    endif
    '''

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: WARN
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text  ::  "pre-steady state warnings"
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd  = commandize( cmd, cmdindent=0, ALLEOL=False )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )

    lout = [comm, pre, cmd, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)

# ----------------------------------------------------------------------

# Text warning, goes to dir_img output
# ['tent_warn_dset']
def apqc_warns_TENT( obase, qcb, qci ):

    opref = '_'.join([obase, qcb, qci]) # full name

    comm  = '''show any TENT warnings from timing_tool.py'''

    pre = '''
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    '''.format( opref )

    cmd = '''
    if ( -f ${tent_warn_dset} ) then
    ~~~~cat ${tent_warn_dset} > ${odir_img}/${opref}.dat
    else
    ~~~~echo " none "  > ${odir_img}/${opref}.dat
    endif
    '''

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: WARN
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    text  ::  "TENT warnings from timing_tool.py"
    EOF
    '''.format(qci, qcb, lahh.qc_blocks[qcb][0], lahh.qc_blocks[qcb][1] )

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm = commentize( comm )
    pre  = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd  = commandize( cmd, cmdindent=0, ALLEOL=False )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )

    lout = [comm, pre, cmd, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)


# ========================== cp jsons ==============================

# cp json(s) to QC_*/ dir
# 1
def apqc_DO_cp_subj_jsons( all_json ):

    comm  = '''preserve subj jsons'''

    pre = '''
    set all_jsons = ( '''

    # When this script is *run* from the AP results directory, all the
    # JSONs should be *in* it, so we just get the tail of whatever
    # path was entered.
    for x in all_json :
        y = x.split('/')
        pre+= y[-1] + ' \n'
    pre+= ' )'

    cmd = '''
    foreach ff ( ${all_jsons} ) 
    ~~~~\cp ${ff} ${odir_info}/.
    end
    '''

    comm = commentize( comm )
    pre  = commandize( pre )
    cmd  = commandize( cmd, cmdindent=0, ALLEOL=False  )

    lout = [comm, pre, cmd]
    return '\n\n'.join(lout)


# ========================== term echo ==============================

# @ss_review_basic dumped to text file
# 1
def apqc_DO_term_ss_review_basic( ):

    comm  = '''basic information from processing'''

    pre = '''
    echo ""
    echo ""
    echo "# +++++++++++ Check output of @ss_review_basic +++++++++++ #"
    echo ""
    '''

    cmd0 = '''
    cat out.ss_review.${subj}.txt
    '''

    comm  = commentize( comm )
    pre   = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    cmd0  = commandize( cmd0, padpost=2 )

    lout = [comm, pre, cmd0]
    return '\n\n'.join(lout)


# ======================== html page title ============================

def apqc_Top_pagetop( opref, qcb, qci, task_name = '' ):

    comm  = '''subject ID for html page title'''

    pre = '''
    set opref = {}
    set tjson  = _tmp.txt
    set ojson  = ${{odir_img}}/${{opref}}.json
    '''.format( opref )

    jsontxt = '''
    cat << EOF >! ${{tjson}}
    itemtype    :: TITLE
    itemid      :: {}
    blockid     :: {}
    blockid_hov :: {}
    title       :: {}
    subj        :: "${{subj}}"
    EOF
    '''.format(qci, qcb, lahh.qc_title[qcb][0], lahh.qc_title[qcb][1] )

    ## !!!!! to be added at some point, from new uvar:
    ##    taskname  ::  task

    jsontxt_cmd = '''
    abids_json_tool.py   
    -overwrite       
    -txt2json              
    -delimiter_major '::'    
    -delimiter_minor ',,'     
    -input  ${tjson}
    -prefix ${ojson}
    '''

    comm  = commentize( comm )
    pre   = commandize( pre, cmdindent=0, 
                       ALIGNASSIGN=True, ALLEOL=False )
    jsontxt = commandize( jsontxt, cmdindent=0, ALLEOL=False )
    jsontxt_cmd  = commandize( jsontxt_cmd, padpost=2 )

    lout = [comm, pre, jsontxt, jsontxt_cmd]
    return '\n\n'.join(lout)

# =========================================================================
# =========================================================================

if __name__ == "__main__":
    # Whee.
    print('Done.')
