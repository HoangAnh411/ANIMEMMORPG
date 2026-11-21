"""C1-only exact Windows argv/process identity checks. No Win32 calls on import."""
import ntpath
import re
import subprocess
from datetime import datetime, timezone

class IdentityError(RuntimeError):
    pass

def render_command(arguments):
    """Quote UE flag values after '=', while preserving the decoded argv values."""
    parts=[]
    for i,arg in enumerate(arguments):
        if i and arg.startswith('-') and '=' in arg:
            name,value=arg.split('=',1);parts.append(name+'='+subprocess.list2cmdline([value]))
        else:parts.append(subprocess.list2cmdline([arg]))
    return ' '.join(parts)

def windows_argv(command):
    """Windows CRT quoting for these ordinary executable/flag arguments.

    Reject malformed quoting instead of guessing. Live tests also compare this
    parser against CommandLineToArgvW; no shell expansion or substring matching.
    """
    result=[];i=0
    while i<len(command):
        while i<len(command) and command[i] in ' \t':i+=1
        if i==len(command):break
        value=[];quoted=False
        while i<len(command) and (quoted or command[i] not in ' \t'):
            slashes=0
            while i<len(command) and command[i]=='\\':slashes+=1;i+=1
            if i<len(command) and command[i]=='"':
                value.extend('\\'*(slashes//2))
                if slashes%2:value.append('"')
                else:quoted=not quoted
                i+=1
            else:
                value.extend('\\'*slashes)
                if i<len(command) and (quoted or command[i] not in ' \t'):value.append(command[i]);i+=1
        if quoted:raise IdentityError('unclosed_quote')
        result.append(''.join(value))
    return result

def path_key(value):
    if not isinstance(value,str) or not ntpath.isabs(value):raise IdentityError('nonabsolute_path')
    return ntpath.normcase(ntpath.normpath(value))

def creation_ticks(value):
    m=re.fullmatch(r'(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)\.(\d{7})(Z|\+00:00)',value or '')
    if not m:raise IdentityError('bad_creation_time')
    dt=datetime.strptime(m[1],'%Y-%m-%dT%H:%M:%S').replace(tzinfo=timezone.utc)
    epoch=datetime(1601,1,1,tzinfo=timezone.utc)
    return int((dt-epoch).total_seconds())*10_000_000+int(m[2])

def verify_identity(record,live):
    if not live:raise IdentityError('process_missing')
    if live.get('pid')!=record['pid']:raise IdentityError('process_pid_mismatch')
    # Only Win32 GetProcessTimes FILETIME is authoritative. CIM CreationDate
    # can lose the final 100-ns digit and is retained as diagnostics only.
    if type(record.get('creationTicks')) is not int or type(live.get('creationTicks')) is not int:
        raise IdentityError('win32_creation_ticks_missing')
    if live['creationTicks']!=record['creationTicks']:
        raise IdentityError('process_creation_mismatch')
    if path_key(live.get('executable'))!=path_key(record['executable']):raise IdentityError('executable_mismatch')
    argv=windows_argv(live.get('commandLine',''))
    if not argv or path_key(argv[0])!=path_key(record['executable']):raise IdentityError('argv_executable_mismatch')
    flags={};positionals=[]
    for arg in argv[1:]:
        if arg.startswith('-'):
            name,sep,value=arg.partition('=');name=name.casefold()
            if name in flags:raise IdentityError('duplicate_argument:'+name)
            flags[name]=value if sep else None
        else:positionals.append(arg)
    sha=record['sourceSHA']
    if not re.fullmatch('[0-9a-fA-F]{40}',sha):raise IdentityError('invalid_expected_sha')
    for flag,key in [('-u02sourcesha','sourceSHA'),('-u02runid','runId')]:
        if flags.get(flag)!=record[key]:raise IdentityError('argument_mismatch:'+flag)
    for flag,key in [('-userdir','userDir'),('-abslog','log')]:
        if flag not in flags or path_key(flags[flag])!=path_key(record[key]):raise IdentityError('argument_mismatch:'+flag)
    # Require the complete planned argument set, including map, profile and trace policy.
    expected=record['arguments'];expected=expected[1:]
    planned_flags={};planned_positionals=[]
    for arg in expected:
        if arg.startswith('-'):
            name,sep,value=arg.partition('=');name=name.casefold()
            if name in planned_flags:raise IdentityError('duplicate_planned_argument')
            planned_flags[name]=value if sep else None
        else:planned_positionals.append(arg)
    if flags!=planned_flags or positionals!=planned_positionals:raise IdentityError('planned_arguments_mismatch')
    return dict(pid=live['pid'],creationUTC=record['creationUTC'],creationTicks=live['creationTicks'],
                cimCreationUTC=live.get('cimCreationUTC',live.get('creationUTC')),executable=live['executable'],argv=argv)
