<template>
  <div class="flex h-screen w-screen overflow-hidden bg-gray-50">

    <!-- ============ 工程选择欢迎页（覆盖整个画面） ============ -->
    <div v-if="!currentProject" class="flex-1 flex flex-col items-center justify-center bg-gradient-to-br from-indigo-50 to-blue-50">
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-indigo-800 mb-2">🧠 AI Engineer Platform</h1>
        <p class="text-gray-500">选择一个工程开始工作，或创建新的工程</p>
      </div>

      <!-- 新建工程按钮 -->
      <el-button type="primary" size="large" @click="newProjectDialogVisible = true" class="mb-6">
        ➕ 新建工程
      </el-button>

      <!-- 工程列表卡片 -->
      <div v-if="projectList.length > 0" class="w-full max-w-3xl px-6">
        <h3 class="text-sm font-bold text-gray-600 mb-3">📂 最近的工程</h3>
        <div class="grid grid-cols-2 gap-4">
          <div v-for="proj in projectList" :key="proj.id"
               class="bg-white rounded-lg border border-gray-200 p-4 shadow-sm hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer group"
               @click="loadProject(proj.id)">
            <div class="flex justify-between items-start mb-2">
              <h4 class="font-bold text-indigo-700 text-sm truncate flex-1">{{ proj.name }}</h4>
              <el-button size="small" type="danger" text @click.stop="confirmDeleteProject(proj.id, proj.name)" class="opacity-0 group-hover:opacity-100 transition-opacity">🗑️</el-button>
            </div>
            <p class="text-xs text-gray-400 mb-2 line-clamp-2">{{ proj.description || '暂无描述' }}</p>
            <div class="flex justify-between items-center text-[11px] text-gray-400">
              <span>🧩 {{ proj.node_count }} 个节点</span>
              <span>{{ formatTime(proj.updated_at) }}</span>
            </div>
          </div>
        </div>
      </div>
      <div v-else class="text-gray-400 text-sm mt-4">
        还没有任何工程，点击上方按钮创建您的第一个工程吧！
      </div>
    </div>

    <!-- ============ 主工作区（仅当工程已打开时显示） ============ -->
    <template v-if="currentProject">

    <!-- Left Sidebar: Chat/Control Panel -->
    <div class="w-96 bg-white border-r border-gray-200 flex flex-col shadow-sm z-10 shrink-0">
      <div class="p-3 border-b border-gray-200 flex flex-col gap-2">
        <div class="flex justify-between items-center">
          <h1 class="text-lg font-semibold text-gray-800">AI Engineer Platform</h1>
          <div class="flex gap-1">
            <el-button size="small" type="primary" plain @click="drawerVisible = true">👁️ 监听台</el-button>
            <el-button size="small" type="warning" plain @click="addTestNode">🧪 测试</el-button>
          </div>
        </div>
        <!-- 工程状态栏 -->
        <div class="flex items-center gap-2 bg-gray-50 rounded px-2 py-1.5 border border-gray-100">
          <span class="text-xs text-gray-400">📂</span>
          <span class="text-sm font-bold text-indigo-700 truncate flex-1" :title="currentProject.name">{{ currentProject.name }}</span>
          <el-button size="small" type="primary" @click="runAllNodesSequentially" :loading="isProjectRunning" :disabled="nodes.length === 0" title="自上而下顺序、阻塞执行所有节点">🚀 顺序全部执行</el-button>
          <el-button size="small" type="success" plain @click="saveCurrentProject" :loading="isSaving">💾 保存</el-button>
          <el-button size="small" plain @click="closeProject">📁 切换</el-button>
        </div>
      </div>
      
      <!-- Chat Area -->
      <div class="flex-1 p-4 overflow-y-auto bg-gray-50">
        <div class="text-center text-sm text-gray-400 mt-8 mb-4">
          向 AI 发送工程指令，为您生成工作程序节点
        </div>
        
        <div v-for="(log, idx) in chatLogs" :key="idx" class="mb-4 text-sm">
          <div v-if="log.role === 'user'" class="text-blue-600 bg-blue-50 p-2 rounded inline-block shadow-sm">
            {{ log.content }}
          </div>
          <div v-else class="text-gray-700 bg-white p-2 rounded inline-block shadow-sm border border-gray-100 mt-1">
            {{ log.content }}
          </div>
        </div>
      </div>
      
      <!-- Input Area -->
      <div class="p-4 bg-white border-t border-gray-200 flex flex-col gap-3">
        <el-input
          v-model="inputMsg"
          type="textarea"
          :rows="4"
          placeholder="例如：写一个Python脚本，抓取数据并打印出带有关键参数的列表..."
          resize="none"
          :disabled="isGenerating || isPlanning"
        />
        <div class="flex justify-between items-center">
          <span class="text-xs font-mono text-gray-400">SSE Stream Enabled</span>
          <div class="flex gap-2">
            <el-button 
              type="info" 
              plain 
              @click="toggleVoiceInput" 
              :class="{'animate-pulse bg-red-100 border-red-300 text-red-600': isRecording}"
              title="后端音频解析（极高精度，支持中英混杂）"
              :loading="isAudioProcessing"
            >
              {{ isRecording ? '🛑 点击停止并转写' : isAudioProcessing ? '🤔 解析中' : '🎤 语音输入' }}
            </el-button>
            <el-button type="primary" :loading="isPlanning || isGenerating" @click="handleSend">
              {{ isPlanning ? '规划流接载...' : '下达指令' }}
            </el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- Right Area: Vue Flow Canvas -->
    <div class="flex-1 relative bg-gray-100 h-full">
      <VueFlow :nodes="nodes" :edges="edges">
        <!-- 定义自定义的 Python 程序节点视图 -->
        <template #node-python="props">
          <div class="p-3 bg-white border-2 border-indigo-500 rounded-lg shadow-lg w-72">
             <!-- 节点标题（可重命名） -->
             <div class="flex items-center justify-between mb-1">
               <div v-if="renamingNodeId === props.id" class="flex-1 nodrag">
                 <el-input v-model="renamingValue" size="small" @keyup.enter="confirmRename(props.id)" @blur="confirmRename(props.id)" autofocus />
               </div>
               <div v-else class="font-bold text-sm text-indigo-700 truncate flex-1 cursor-pointer" :title="props.data.label || props.data.prompt" @dblclick.stop="startRename(props.id, props.data.label || props.data.prompt)">
                 🧩 {{ props.data.label || props.data.prompt }}
               </div>
               <el-button size="small" type="danger" text @click.stop="confirmDeleteNode(props.id)" class="ml-1 nodrag" title="删除节点">✕</el-button>
             </div>
             
             <!-- 业务逻辑执行结构流指针 -->
             <div v-if="props.data.steps && props.data.steps.length > 0" class="mb-3 mt-2 nodrag">
                <details class="text-xs bg-gray-50 border border-gray-200 rounded p-1.5 cursor-pointer hover:bg-gray-100 transition-colors shadow-sm">
                   <summary class="font-bold text-gray-600 outline-none select-none px-1 flex items-center justify-between">
                     <span>⚙️ 执行步骤结构 ({{ props.data.steps.length }}步)</span>
                     <span v-if="props.data.running" class="text-[10px] text-yellow-600 animate-pulse">正在运行...</span>
                     <span v-else-if="props.data.activeStep === props.data.steps.length - 1 && !props.data.isError" class="text-[10px] text-green-600">已完成</span>
                   </summary>
                   <div class="space-y-1 mt-2 cursor-default bg-white p-1.5 rounded border border-gray-100">
                      <div v-for="(step, idx) in props.data.steps" :key="idx" class="text-[11px] px-2 py-1 flex items-center gap-2 rounded transition-colors duration-300"
                         :class="{
                           'bg-yellow-100 text-yellow-800 font-bold border border-yellow-300 shadow-sm animate-pulse': props.data.activeStep === idx && !props.data.isError && props.data.running,
                           'bg-yellow-50 text-yellow-700': props.data.activeStep === idx && !props.data.isError && !props.data.running,
                           'bg-green-100 text-green-800 font-bold': props.data.activeStep > idx || (!props.data.running && !props.data.isError && props.data.activeStep === props.data.steps.length - 1),
                           'bg-red-100 text-red-800 font-bold border border-red-300': props.data.isError && props.data.activeStep === idx,
                           'bg-gray-100 text-gray-500': props.data.activeStep < idx && props.data.activeStep !== props.data.steps.length - 1
                         }">
                         <span class="w-16 whitespace-nowrap">
                           <template v-if="props.data.activeStep === idx && props.data.running && !props.data.isError">👉 运行中</template>
                           <template v-else-if="props.data.activeStep > idx || (!props.data.running && !props.data.isError && props.data.activeStep === props.data.steps.length - 1)">✅ 已完成</template>
                           <template v-else-if="props.data.isError && props.data.activeStep === idx">❌ 崩溃停机</template>
                           <template v-else>⏳ 待执行</template>
                         </span>
                         <span class="truncate flex-1" :title="step">{{ step }}</span>
                      </div>
                   </div>
                </details>
             </div>

             <!-- 动态参数绑定区域 -->
             <div v-if="props.data.parameters && props.data.parameters.length > 0" class="mb-3 nodrag">
                <details class="text-xs bg-indigo-50 border border-indigo-100 rounded p-1.5 cursor-pointer hover:bg-indigo-100 transition-colors shadow-sm">
                   <summary class="font-semibold text-indigo-800 outline-none select-none px-1 flex items-center justify-between">
                     <span>🔧 运行外部参数 ({{ props.data.parameters.length }}个)</span>
                   </summary>
                   <div class="space-y-2 mt-2 cursor-default bg-white p-2 rounded border border-indigo-50">
                       <div v-for="p in props.data.parameters" :key="p.name" class="flex items-center justify-between">
                           <span class="text-gray-700 truncate w-20 flex-shrink-0" :title="p.description">{{ p.name }}:</span>
                           <el-input size="small" v-model="props.data.paramValues[p.name]" class="w-36" :placeholder="String(p.default)" />
                       </div>
                   </div>
                </details>
             </div>
             
             <!-- 代码预览区 -->
             <div class="text-[10px] text-gray-600 mb-3 h-16 overflow-y-auto bg-gray-50 p-1 border rounded font-mono nodrag nowheel">
               {{ props.data.code }}
             </div>
             
             <!-- 动作区 -->
             <div class="flex flex-wrap gap-2 justify-between items-center mt-2 nodrag">
                <el-button-group>
                  <el-button size="small" type="success" plain :loading="props.data.running" @click.stop="runNode(props.id, props.data.code, props.data.paramValues, false)" title="无追踪，追求速度的极速原生运行">
                    ⚡ 极速执行
                  </el-button>
                  <el-button size="small" type="success" :loading="props.data.running" @click.stop="runNode(props.id, props.data.code, props.data.paramValues, true)">
                    ▶ 演示执行
                  </el-button>
                </el-button-group>
                <el-button size="small" type="info" plain @click.stop="openNodeDir(props.data.paramValues)" title="尝试调用底层操作系统浏览器打开此节点约定的工作输出目录 (需参数中有 work_dir 等变量)">
                  📁 目录
                </el-button>
                <el-button size="small" type="warning" plain @click.stop="openCodeEditor(props.id, props.data.code)">
                  ✍️ 修改代码
                </el-button>
                <el-button size="small" type="info" plain @click.stop="showCopyNodeDialog(props.id)" title="复制到其他工程">
                  📋 复制
                </el-button>
                <el-button v-if="props.data.output" size="small" type="info" plain @click.stop="viewOutput(props.id, props.data.output, props.data.isError)">
                  中间数据
                </el-button>
             </div>
          </div>
        </template>

        <Background />
        <Controls />
      </VueFlow>
    </div>

    </template><!-- v-if="currentProject" -->
  </div>

  <!-- 新建工程对话框 -->
  <el-dialog v-model="newProjectDialogVisible" title="➕ 新建工程" width="450px" :modal="false" append-to-body draggable>
    <el-form label-position="top">
      <el-form-item label="工程名称">
        <el-input v-model="newProjectName" placeholder="例如：销售数据分析流水线" maxlength="50" show-word-limit />
      </el-form-item>
      <el-form-item label="工程描述（可选）">
        <el-input v-model="newProjectDesc" type="textarea" :rows="3" placeholder="简要描述这个工程的用途和目标..." />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="newProjectDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="createProject" :disabled="!newProjectName.trim()">创建并进入</el-button>
    </template>
  </el-dialog>

  <!-- 复制节点到其他工程对话框 -->
  <el-dialog v-model="copyNodeDialogVisible" title="📋 复制节点到其他工程" width="450px" :modal="false" append-to-body draggable>
    <div v-if="otherProjects.length === 0" class="text-center text-gray-400 py-4">
      没有其他工程可以复制到，请先创建一个新工程。
    </div>
    <div v-else class="space-y-2">
      <div v-for="proj in otherProjects" :key="proj.id"
           class="p-3 border rounded cursor-pointer hover:bg-indigo-50 hover:border-indigo-300 transition-colors"
           @click="doCopyNode(proj.id)">
        <div class="font-bold text-sm text-indigo-700">{{ proj.name }}</div>
        <div class="text-xs text-gray-400">{{ proj.description || '暂无描述' }} · {{ proj.node_count }} 个节点</div>
      </div>
    </div>
  </el-dialog>

  <!-- 沙箱实时输出控制台 -->
  <el-dialog v-model="consoleVisible" title="💻 实况沙箱物理终端 (Sandbox Terminal)" width="70%" draggable class="resize-y overflow-hidden" :modal="false" append-to-body :close-on-click-modal="false" top="5vh">
    <div class="mb-2 flex justify-between items-center">
       <span class="text-sm text-gray-500">连接到物理隔离的临时计算环境，当前状态: <span class="font-bold">{{ isSandboxRunning ? '🟢 正在执行' : '🔴 已断开' }}</span></span>
       <div class="flex items-center gap-2">
         <el-button v-if="currentIsError && !isSandboxRunning && runningNodeId" size="small" type="primary" @click="openAiFixDialog">🤖 AI 智能修复</el-button>
         <el-tag :type="currentIsError ? 'danger': 'success'" v-if="!isSandboxRunning">{{ currentIsError ? '存在异常退出' : '安全退出' }}</el-tag>
       </div>
    </div>
    <div class="bg-black text-green-400 p-4 rounded overflow-y-auto font-mono text-sm shadow-inner" style="min-height: 400px; max-height: 600px;" ref="consoleBox">
       <div v-for="(line, idx) in consoleLogs" :key="idx" class="whitespace-pre-wrap break-all leading-tight">{{ line }}</div>
       <div v-if="isSandboxRunning" class="animate-pulse inline-block w-2 bg-green-400 h-4 align-middle mt-1"></div>
    </div>
  </el-dialog>

  <!-- AI 智能修复对话框 -->
  <el-dialog v-model="aiFixDialogVisible" title="🤖 AI 智能代码修复" width="55%" draggable :modal="false" append-to-body top="10vh">
    <div class="space-y-4">
      <div>
        <div class="text-xs font-bold text-gray-600 mb-1">📜 终端输出（将自动发送给 AI）</div>
        <div class="bg-gray-900 text-green-400 p-3 rounded font-mono text-xs max-h-40 overflow-y-auto">
          <div v-for="(line, idx) in consoleLogs" :key="idx" class="whitespace-pre-wrap break-all leading-tight">{{ line }}</div>
        </div>
      </div>
      <div>
        <div class="text-xs font-bold text-gray-600 mb-1">💬 您的补充说明（可选）</div>
        <el-input v-model="aiFixUserMsg" type="textarea" :rows="3" placeholder="例如：这个报错应该是编码问题，帮我兼容 GBK 和 UTF-8..." />
      </div>
      <div v-if="isAiFixing" class="bg-blue-50 border border-blue-200 rounded p-3">
        <div class="text-xs font-bold text-blue-700 mb-2">🔄 AI 正在审查并修复代码...</div>
        <div class="text-xs text-blue-600 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">{{ aiFixPreview }}<span class="animate-pulse">_</span></div>
      </div>
    </div>
    <template #footer>
      <el-button @click="aiFixDialogVisible = false" :disabled="isAiFixing">取消</el-button>
      <el-button type="primary" @click="submitAiFix" :loading="isAiFixing">
        {{ isAiFixing ? 'AI 修复中...' : '🚀 发送给 AI 修复' }}
      </el-button>
    </template>
  </el-dialog>

  <!-- Plan 确认看板 -->
  <el-dialog v-model="planDialogVisible" title="工程师方案复核 (Interactive Planner)" width="60%" draggable :modal="false" append-to-body>
    <div class="max-h-[65vh] overflow-y-auto pr-2 pb-1">
      <div v-if="currentPlan" class="text-sm text-gray-700 space-y-4">
        <!-- 手工编辑步骤 -->
      <div>
        <h3 class="font-bold text-gray-900 border-b pb-1 mb-2 flex justify-between">
          1. 逻辑执行步骤预判
          <el-button size="small" text type="primary" @click="currentPlan.steps.push('新步骤')">+ 增加步骤</el-button>
        </h3>
        <div class="space-y-2">
           <div v-for="(step, idx) in currentPlan.steps" :key="'step'+idx" class="flex gap-2 items-start">
             <span class="mt-1 font-bold">{{ Number(idx) + 1 }}.</span>
             <el-input type="textarea" autosize v-model="currentPlan.steps[idx]" />
             <el-button type="danger" text @click="currentPlan.steps.splice(idx, 1)">删</el-button>
           </div>
        </div>
      </div>
      <!-- 手工编辑参数 -->
      <div>
        <h3 class="font-bold text-gray-900 border-b pb-1 mb-2 flex justify-between">
          2. 全局动态参数管理 (画布节点输入框来源)
          <el-button size="small" text type="primary" @click="addParameter">+ 手动加参</el-button>
        </h3>
        <el-table :data="currentPlan.parameters" style="width: 100%" size="small" border>
          <el-table-column label="变量名(纯英文)" width="150">
             <template #default="scope"><el-input v-model="scope.row.name" size="small" /></template>
          </el-table-column>
          <el-table-column label="类型" width="100">
             <template #default="scope"><el-input v-model="scope.row.type" size="small" /></template>
          </el-table-column>
          <el-table-column label="默认值" width="120">
             <template #default="scope"><el-input v-model="scope.row.default" size="small" /></template>
          </el-table-column>
          <el-table-column label="变量说明含义">
             <template #default="scope"><el-input v-model="scope.row.description" size="small" /></template>
          </el-table-column>
          <el-table-column label="操作" width="60" align="center">
             <template #default="scope">
                <el-button type="danger" text @click="currentPlan.parameters.splice(scope.$index, 1)">删</el-button>
             </template>
          </el-table-column>
        </el-table>
      </div>
      
      <!-- 第三方依赖展示墙 -->
      <div v-if="currentPlan.dependencies !== undefined" class="mt-4">
         <h3 class="font-bold text-gray-900 border-b pb-1 mb-2 flex justify-between items-center text-sm">
            3. 沙箱独立子环境防幻觉拦截名单 (Dependencies)
            <div class="flex gap-2">
              <el-input size="small" v-model="newDepName" placeholder="库名(小写)" class="w-24" />
              <el-button size="small" type="primary" text @click="addDependency">+ 强制补包</el-button>
            </div>
         </h3>
         <div class="flex gap-2 flex-wrap min-h-[30px] p-2 bg-gray-50 border border-gray-100 rounded">
            <template v-if="currentPlan.dependencies.length">
              <el-tag
                v-for="(dep, idx) in currentPlan.dependencies"
                :key="idx"
                closable
                type="warning"
                @close="currentPlan.dependencies.splice(idx, 1)"
              >
                {{ dep }}
              </el-tag>
            </template>
            <span v-else class="text-xs text-gray-500">此节点纯净执行，除内置库外不拉取任何外部冗余文件。速度起飞。</span>
         </div>
      </div>
      
      <!-- AI 辅助重塑区 -->
      <div class="bg-blue-50 p-3 rounded border border-blue-100 flex items-center gap-3">
        <span class="text-blue-700 whitespace-nowrap font-bold">🤖 AI 微调大师:</span>
        <el-input v-model="refineMsg" placeholder="例如：再帮我加一个存储过滤后的文件路径参数..." size="small" @keyup.enter="handleRefine" :disabled="isRefining" />
        <el-button type="primary" size="small" :loading="isRefining" @click="handleRefine">推入流逝生成</el-button>
      </div>

      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="planDialogVisible = false">丢弃当前方案</el-button>
        <el-button type="success" @click="confirmPlan" :loading="isGenerating">
          ✅ 确认最终方案并生成底层代码
        </el-button>
      </div>
    </template>
  </el-dialog>

  <!-- 代码编辑面板 (Monaco Editor) + AI 对话 -->
  <el-dialog v-model="codeEditorVisible" title="节点代码深度编辑 (Monaco)" width="75%" destroy-on-close draggable top="3vh" :modal="false" append-to-body :close-on-click-modal="false">
    <div class="h-[55vh] border rounded overflow-hidden resize-y flex flex-col" style="min-height: 300px; max-height: 75vh;">
      <VueMonacoEditor 
        v-model:value="editingCode"
        language="python"
        theme="vs-dark"
        :options="{ minimap: { enabled: false }, fontSize: 13, tabSize: 4 }"
      />
    </div>
    <!-- AI 对话输入区 -->
    <div class="mt-3 bg-blue-50 border border-blue-200 rounded p-3">
      <div class="flex items-center gap-2 mb-2">
        <span class="text-xs font-bold text-blue-700">🤖 AI 编程助手</span>
        <span class="text-[11px] text-blue-400">用自然语言告诉 AI 怎么改代码，AI 会直接修改编辑器中的内容</span>
      </div>
      <div class="flex gap-2">
        <el-input v-model="editorAiMsg" placeholder="例如：帮我加一个异常处理 / 把循环改成列表推导式 / 增加日志输出..." size="small" @keyup.enter="submitEditorAiChat" :disabled="isEditorAiChatting" class="flex-1" />
        <el-button type="primary" size="small" :loading="isEditorAiChatting" @click="submitEditorAiChat" :disabled="!editorAiMsg.trim()">
          {{ isEditorAiChatting ? '生成中...' : '✨ AI 修改' }}
        </el-button>
      </div>
    </div>
    <template #footer>
       <div class="flex justify-between items-center">
         <span class="text-xs text-gray-500">修改后将直接影响本节点下次的运行逻辑。如果您添加了新参数变量，记得去更新节点的参数列表。</span>
         <div>
            <el-button @click="codeEditorVisible = false">取消修改</el-button>
            <el-button type="primary" @click="saveEditedCode">💾 覆盖并保存</el-button>
         </div>
       </div>
    </template>
  </el-dialog>
  
  <!-- AI 黑盒打字机探针 (纯 DIV 侧边面板) -->
  <Transition name="slide-panel">
    <div v-if="drawerVisible" class="fixed top-0 right-0 h-full bg-white shadow-2xl border-l border-gray-300 flex flex-col" style="width: 30%; z-index: 10;">
      <div class="p-3 border-b border-gray-200 flex justify-between items-center shrink-0">
        <span class="font-bold text-gray-800 text-sm">🧠 引擎透明拦截网 (SSE Stream)</span>
        <el-button size="small" text @click="drawerVisible = false">✕ 关闭</el-button>
      </div>
      <div class="flex-1 overflow-auto bg-gray-900 rounded m-2 p-4 text-xs font-mono">
        <div v-if="!systemPromptLog && !aiOutputLog" class="text-gray-500 mt-4 text-center">
            当前没有模型调用传输隧道在进行中...<br/>下令执行任务后，这里会拦截并实时打印包内内容。
        </div>
        <template v-else>
            <div class="text-yellow-400 mb-2"># ----- [SYSTEM PROMPT ENVELOPE] -----</div>
            <div class="text-green-300 font-bold mb-6 whitespace-pre-wrap">{{ systemPromptLog }}</div>
            
            <div class="text-yellow-400 mb-2 mt-4"># ----- [LIVE RECEIVING STREAM...] -----</div>
            <div class="text-blue-300 whitespace-pre-wrap">{{ aiOutputLog }}<span class="animate-pulse font-bold text-lg">_</span></div>
        </template>
      </div>
      <div class="text-xs text-gray-500 p-2 shrink-0">
        该面板实时拦截后端与模型间的 Server-Sent Events 流式字节包。你看到的代码是一个字一个字传过来的。
      </div>
    </div>
  </Transition>

</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { VueFlow, useVueFlow } from '@vue-flow/core'
import { Background } from '@vue-flow/background'
import { Controls } from '@vue-flow/controls'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { VueMonacoEditor } from '@guolao/vue-monaco-editor'

// 根据当前访问的 IP/域名动态拼接后端地址，适配局域网访问
const API_BASE = `http://${window.location.hostname}:8000/api`

// ==================== 工程管理状态 ====================
const currentProject = ref<any>(null)
const projectList = ref<any[]>([])
const newProjectDialogVisible = ref(false)
const newProjectName = ref('')
const newProjectDesc = ref('')
const isSaving = ref(false)
const isProjectRunning = ref(false)

// ==================== 节点操作状态 ====================
const renamingNodeId = ref('')
const renamingValue = ref('')
const copyNodeDialogVisible = ref(false)
const copyingNodeId = ref('')
const otherProjects = computed(() => projectList.value.filter(p => p.id !== currentProject.value?.id))

// Stream 透明侦测器状态
const drawerVisible = ref(false)
const systemPromptLog = ref('')
const aiOutputLog = ref('')

const inputMsg = ref('')
const isPlanning = ref(false)
const isGenerating = ref(false)
const chatLogs = ref<{role: string, content: string}[]>([])

// ==================== 语音识别状态 ====================
const isRecording = ref(false)
const isAudioProcessing = ref(false)
let mediaRecorder: MediaRecorder | null = null
let audioChunks: Blob[] = []

const startRecording = async () => {
    try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        mediaRecorder = new MediaRecorder(stream)
        audioChunks = []
        
        mediaRecorder.ondataavailable = (event) => {
            if (event.data.size > 0) {
                audioChunks.push(event.data)
            }
        }
        
        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' })
            const formData = new FormData()
            formData.append('file', audioBlob, 'record.webm')
            
            isAudioProcessing.value = true
            isRecording.value = false
            
            try {
                const response = await fetch(`${API_BASE}/audio/transcribe`, {
                    method: 'POST',
                    body: formData
                })
                if (!response.ok) throw new Error(`HTTP ${response.status}`)
                const result = await response.json()
                if (result.text) {
                    inputMsg.value = (inputMsg.value ? inputMsg.value + ' ' : '') + result.text
                    ElMessage.success("🎙️ 分析完毕！文字已追加。")
                } else {
                    ElMessage.warning('未能识别到语音或输入太短')
                }
            } catch (e: any) {
                ElMessage.error('🎙️ 处理失败：请检查后端 faster-whisper 是否就绪。异常内容：' + (e.message || e))
            } finally {
                isAudioProcessing.value = false
            }
            
            // 释放麦克风硬件通道
            stream.getTracks().forEach(track => track.stop())
        }
        
        mediaRecorder.start()
        isRecording.value = true
    } catch (err: any) {
        if (err.name === 'NotAllowedError') {
            ElMessage.error('🎙️ 麦克风权限被拒绝，请在浏览器最上方的地址栏左侧，允许此网站的麦克风权限。')
        } else {
            ElMessage.error('🎙️ 麦克风硬件不可用：' + err.message)
        }
    }
}

const toggleVoiceInput = () => {
    if (isRecording.value && mediaRecorder && mediaRecorder.state !== 'inactive') {
        mediaRecorder.stop()
    } else {
        startRecording()
    }
}

// 画布数据
const nodes = ref<any[]>([])
const edges = ref<any[]>([])
const { addNodes, addEdges } = useVueFlow()
let nodeCounter = 1;
let prevNodeId = '';

const consoleVisible = ref(false)
const consoleLogs = ref<string[]>([])
const isSandboxRunning = ref(false)
const consoleBox = ref<any>(null)
const currentIsError = ref(false)

const planDialogVisible = ref(false)
const currentPlan = ref<any>(null)
const unconfirmedPrompt = ref('')

const refineMsg = ref('')
const isRefining = ref(false)

const codeEditorVisible = ref(false)
const editingNodeId = ref('')
const editingCode = ref('')

// AI 修复状态
const aiFixDialogVisible = ref(false)
const aiFixUserMsg = ref('')
const isAiFixing = ref(false)
const aiFixPreview = ref('')
const runningNodeId = ref('')

// 编辑器内 AI 对话状态
const editorAiMsg = ref('')
const isEditorAiChatting = ref(false)

// ==================== 工程管理方法 ====================

const formatTime = (iso: string) => {
  if (!iso) return ''
  const d = new Date(iso)
  return `${d.getMonth()+1}/${d.getDate()} ${d.getHours()}:${String(d.getMinutes()).padStart(2,'0')}`
}

const fetchProjectList = async () => {
  try {
    const res = await axios.get(`${API_BASE}/projects`)
    projectList.value = res.data.projects || []
  } catch (e) {
    console.error('获取工程列表失败', e)
  }
}

const createProject = async () => {
  if (!newProjectName.value.trim()) return
  try {
    const res = await axios.post(`${API_BASE}/projects`, {
      name: newProjectName.value.trim(),
      description: newProjectDesc.value.trim()
    })
    const proj = res.data.project
    newProjectDialogVisible.value = false
    newProjectName.value = ''
    newProjectDesc.value = ''
    // 直接进入新工程
    currentProject.value = proj
    resetWorkspace()
    ElMessage.success(`工程「${proj.name}」创建成功！`)
    await fetchProjectList()
  } catch (e: any) {
    ElMessage.error('创建工程失败：' + (e.message || '未知错误'))
  }
}

const loadProject = async (projectId: string) => {
  try {
    const res = await axios.get(`${API_BASE}/projects/${projectId}`)
    const proj = res.data.project
    currentProject.value = { id: proj.id, name: proj.name, description: proj.description }
    
    // 恢复画布数据
    resetWorkspace()
    chatLogs.value = proj.chat_logs || []
    
    // 恢复节点
    for (const n of (proj.nodes || [])) {
      const paramValues: Record<string, any> = {}
      const params = n.parameters || []
      params.forEach((p: any) => {
        paramValues[p.name] = p.default !== undefined ? String(p.default) : ''
      })
      nodes.value.push({
        id: n.id,
        type: 'python',
        position: { x: n.position_x, y: n.position_y },
        data: {
          label: n.label || n.prompt,
          prompt: n.prompt,
          code: n.code,
          parameters: params,
          dependencies: n.dependencies || [],
          steps: n.steps || [],
          activeStep: -1,
          paramValues: paramValues,
          running: false,
          output: null,
          isError: false
        }
      })
      nodeCounter = Math.max(nodeCounter, parseInt(n.id.split('_').pop()) + 1 || nodeCounter)
    }
    
    // 恢复连线
    for (const e of (proj.edges || [])) {
      edges.value.push({ id: e.id, source: e.source, target: e.target })
    }
    
    // 设置 prevNodeId 为最后一个节点
    if (nodes.value.length > 0) {
      prevNodeId = nodes.value[nodes.value.length - 1].id
    }
    
    ElMessage.success(`工程「${proj.name}」加载完毕！`)
  } catch (e: any) {
    ElMessage.error('加载工程失败：' + (e.message || '未知错误'))
  }
}

const resetWorkspace = () => {
  nodes.value = []
  edges.value = []
  chatLogs.value = []
  nodeCounter = 1
  prevNodeId = ''
  systemPromptLog.value = ''
  aiOutputLog.value = ''
}

const closeProject = async () => {
  try {
    await ElMessageBox.confirm('是否先保存当前工程？', '切换工程', {
      confirmButtonText: '保存并切换',
      cancelButtonText: '直接切换',
      distinguishCancelAndClose: true
    })
    await saveCurrentProject()
  } catch (action) {
    // 用户选择直接切换或关闭对话框
  }
  currentProject.value = null
  resetWorkspace()
  await fetchProjectList()
}

const showProjectManager = async () => {
  await fetchProjectList()
  // 如果当前有工程，先关闭
  if (currentProject.value) {
    await closeProject()
  }
}

const saveCurrentProject = async () => {
  if (!currentProject.value) return
  isSaving.value = true
  try {
    const payload = {
      name: currentProject.value.name,
      description: currentProject.value.description || '',
      chat_logs: chatLogs.value,
      nodes: nodes.value.map(n => ({
        id: n.id,
        label: n.data.label || n.data.prompt,
        prompt: n.data.prompt,
        code: n.data.code,
        parameters: n.data.parameters || [],
        dependencies: n.data.dependencies || [],
        steps: n.data.steps || [],
        position_x: n.position.x,
        position_y: n.position.y,
      })),
      edges: edges.value.map(e => ({
        id: e.id,
        source: e.source,
        target: e.target
      }))
    }
    await axios.put(`${API_BASE}/projects/${currentProject.value.id}`, payload)
    ElMessage.success('💾 工程已保存！')
  } catch (e: any) {
    ElMessage.error('保存失败：' + (e.message || '未知错误'))
  } finally {
    isSaving.value = false
  }
}

const confirmDeleteProject = async (projectId: string, projectName: string) => {
  try {
    await ElMessageBox.confirm(`确定要永久删除工程「${projectName}」吗？\n此操作不可撤销，所有节点和代码将被彻底清除。`, '⚠️ 删除确认', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await axios.delete(`${API_BASE}/projects/${projectId}`)
    ElMessage.success('工程已删除')
    await fetchProjectList()
  } catch (e) {
    // 用户取消
  }
}

// ==================== 节点操作方法 ====================

const startRename = (nodeId: string, currentLabel: string) => {
  renamingNodeId.value = nodeId
  renamingValue.value = currentLabel
}

const confirmRename = (nodeId: string) => {
  if (renamingValue.value.trim()) {
    const node = nodes.value.find(n => n.id === nodeId)
    if (node) {
      node.data.label = renamingValue.value.trim()
    }
  }
  renamingNodeId.value = ''
}

const confirmDeleteNode = async (nodeId: string) => {
  try {
    await ElMessageBox.confirm('确定要删除这个节点吗？相关连线也会一并清除。', '删除节点', {
      confirmButtonText: '确定删除',
      cancelButtonText: '取消',
      type: 'warning'
    })
    // 删除节点
    nodes.value = nodes.value.filter(n => n.id !== nodeId)
    // 删除关联连线
    edges.value = edges.value.filter(e => e.source !== nodeId && e.target !== nodeId)
    // 更新 prevNodeId
    if (prevNodeId === nodeId) {
      prevNodeId = nodes.value.length > 0 ? nodes.value[nodes.value.length - 1].id : ''
    }
    ElMessage.success('节点已删除')
  } catch (e) {
    // 用户取消
  }
}

const showCopyNodeDialog = async (nodeId: string) => {
  copyingNodeId.value = nodeId
  await fetchProjectList()
  copyNodeDialogVisible.value = true
}

const doCopyNode = async (targetProjectId: string) => {
  try {
    await axios.post(`${API_BASE}/projects/${currentProject.value.id}/copy-node`, {
      source_node_id: copyingNodeId.value,
      target_project_id: targetProjectId
    })
    copyNodeDialogVisible.value = false
    ElMessage.success('节点已复制到目标工程！')
    await fetchProjectList()
  } catch (e: any) {
    ElMessage.error('复制失败：' + (e.message || '未知错误'))
  }
}

// ==================== SSE 拉流引擎封装 ====================
const fetchStream = async (url: string, bodyObj: any) => {
    systemPromptLog.value = '';
    aiOutputLog.value = '';
    
    let jsonTextStr = '';
    try {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyObj)
        });
        
        if (!response.body) throw new Error('流媒体握手失败，环境不支持或断连');
        
        const reader = response.body.getReader();
        const decoder = new TextDecoder("utf-8");
        let buffer = '';
        
        while (true) {
            const { value, done } = await reader.read();
            if (done) break;
            
            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split('\n\n');
            buffer = lines.pop() || '';
            
            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    const dataStr = line.substring(6);
                    if (dataStr === '[DONE]') break;
                    try {
                        const data = JSON.parse(dataStr);
                        if (data.type === 'system_prompt') {
                            systemPromptLog.value = data.content;
                        } else if (data.type === 'chunk') {
                            aiOutputLog.value += data.content;
                            jsonTextStr += data.content;
                        } else if (data.type === 'error') {
                            throw new Error(data.content);
                        }
                    } catch(e) {}
                }
            }
        }
        return jsonTextStr;
    } catch(err: any) {
        throw new Error(err.message || '网络流式读取崩溃');
    }
}

// ==================== 已有功能方法 ====================

const openCodeEditor = (nodeId: string, currentCode: string) => {
  editingNodeId.value = nodeId
  editingCode.value = currentCode
  codeEditorVisible.value = true
}

const saveEditedCode = () => {
  const node = nodes.value.find(n => n.id === editingNodeId.value)
  if (node) {
    node.data.code = editingCode.value
    ElMessage.success("节点自定义代码已保存生效！")
  }
  codeEditorVisible.value = false
}

const newDepName = ref('')

const addDependency = () => {
   if (!newDepName.value.trim()) return
   if (!currentPlan.value.dependencies) {
      currentPlan.value.dependencies = []
   }
   currentPlan.value.dependencies.push(newDepName.value.trim())
   newDepName.value = ''
}

const addParameter = () => {
   if (!currentPlan.value.parameters) {
      currentPlan.value.parameters = []
   }
   currentPlan.value.parameters.push({name: 'new_param', type: 'string', default: '', description: ''})
}

const parseVulnerableJson = (rawStr: string) => {
    let clean = rawStr.trim();
    if(clean.startsWith('```json')) clean = clean.substring(7);
    if(clean.startsWith('```')) clean = clean.substring(3);
    if(clean.endsWith('```')) clean = clean.substring(0, clean.length - 3);
    return JSON.parse(clean.trim());
}

const handleRefine = async () => {
  if (!refineMsg.value.trim() || !currentPlan.value) return;
  isRefining.value = true
  const promptTxt = refineMsg.value
  refineMsg.value = ''
  
  try {
    chatLogs.value.push({ role: 'user', content: `(微调要求)：${promptTxt}` })
    drawerVisible.value = true
    
    const rawResult = await fetchStream(`${API_BASE}/kimi/plan_refine_stream`, { 
        prompt: promptTxt,
        old_plan: currentPlan.value 
    })
    
    const parsedPlan = parseVulnerableJson(rawResult)
    if (parsedPlan.error) throw new Error(parsedPlan.error)
    
    currentPlan.value = parsedPlan
    chatLogs.value.push({ role: 'system', content: `流式装载 AI 建议完毕。已更新面板里的表格方案。` })
  } catch (error: any) {
    ElMessage.error("流式微调失败：" + error.message)
  } finally {
    isRefining.value = false
  }
}

const handleSend = async () => {
  if (!inputMsg.value.trim()) return;
  const prompt = inputMsg.value
  inputMsg.value = ''
  
  unconfirmedPrompt.value = prompt
  chatLogs.value.push({ role: 'user', content: prompt })
  isPlanning.value = true
  
  try {
    chatLogs.value.push({ role: 'system', content: `开始窃听底层通信，打字机流接载中...` })
    drawerVisible.value = true
    
    const rawResult = await fetchStream(`${API_BASE}/kimi/plan_stream`, { prompt })
    const parsedPlan = parseVulnerableJson(rawResult)
    if (parsedPlan.error) throw new Error(parsedPlan.error)
    
    currentPlan.value = parsedPlan
    planDialogVisible.value = true
    
  } catch (error: any) {
    ElMessage.error("计划流接收失败：" + error.message)
    chatLogs.value.push({ role: 'system', content: `[Error] ${error.message}` })
  } finally {
    isPlanning.value = false
  }
}

const confirmPlan = async () => {
  isGenerating.value = true
  try {
    drawerVisible.value = true
    
    const pythonCode = await fetchStream(`${API_BASE}/kimi/generate_stream`, { 
      prompt: unconfirmedPrompt.value,
      plan: currentPlan.value 
    })
    
    chatLogs.value.push({ role: 'system', content: `SSE 传输通过！KIMI成功打字输出了专属处理代码。` })
    
    const paramValues: Record<string, string | number> = {}
    if (currentPlan.value.parameters) {
      currentPlan.value.parameters.forEach((p: any) => {
        paramValues[p.name] = p.default !== undefined ? String(p.default) : ''
      })
    }
    
    const newNodeId = `node_${Date.now().toString(36)}_${nodeCounter++}`
    const newNode = {
      id: newNodeId,
      type: 'python',
      position: { x: 300, y: 10 + (nodeCounter - 1) * 230 },
      data: {
        label: unconfirmedPrompt.value.length > 15 ? unconfirmedPrompt.value.substring(0, 15) + '...' : unconfirmedPrompt.value,
        prompt: unconfirmedPrompt.value,
        code: pythonCode,
        parameters: currentPlan.value.parameters,
        dependencies: currentPlan.value.dependencies || [],
        steps: currentPlan.value.steps || [],
        activeStep: -1,
        paramValues: paramValues,
        running: false,
        output: null,
        isError: false
      }
    }
    nodes.value.push(newNode)
    
    if (prevNodeId) {
       edges.value.push({ id: `e${prevNodeId}-${newNodeId}`, source: prevNodeId, target: newNodeId })
    }
    prevNodeId = newNodeId
    
    planDialogVisible.value = false

  } catch (error: any) {
    ElMessage.error("流式代码生成崩溃：" + error.message)
  } finally {
    isGenerating.value = false
  }
}

const addTestNode = () => {
  const testCode = `# [__BLOCK_MARK__: 0] 初始化并打印欢迎信息
print("=" * 40)
print("🚀 测试节点启动成功！")
print("=" * 40)

# [__BLOCK_MARK__: 1] 模拟数据处理
data = [i ** 2 for i in range(1, 6)]
print(f"\\n📊 生成测试数据: {data}")
print(f"📈 数据总和: {sum(data)}")
print(f"📉 数据平均: {sum(data)/len(data)}")

# [__BLOCK_MARK__: 2] 输出最终结果
print("\\n✅ 所有测试步骤执行完毕，系统运行正常！")
print("⏱️  节点生命周期结束。")
`
  const newNodeId = `node_${Date.now().toString(36)}_${nodeCounter++}`
  const newNode = {
    id: newNodeId,
    type: 'python',
    position: { x: 300, y: 10 + (nodeCounter - 1) * 230 },
    data: {
      label: '🧪 调试测试节点',
      prompt: '🧪 调试测试节点',
      code: testCode,
      parameters: [],
      dependencies: [],
      steps: ['初始化并打印欢迎信息', '模拟数据处理', '输出最终结果'],
      activeStep: -1,
      paramValues: {},
      running: false,
      output: null,
      isError: false
    }
  }
  nodes.value.push(newNode)
  if (prevNodeId) {
    edges.value.push({ id: `e${prevNodeId}-${newNodeId}`, source: prevNodeId, target: newNodeId })
  }
  prevNodeId = newNodeId
  ElMessage.success('已创建测试节点，可直接点击执行按钮调试！')
}

const runNode = async (nodeId: string, code: string, paramValues: any, demoMode: boolean) => {
  const node = nodes.value.find(n => n.id === nodeId)
  if (!node) return;
  
  node.data.running = true;
  node.data.activeStep = -1;
  consoleVisible.value = true;
  isSandboxRunning.value = true;
  runningNodeId.value = nodeId;
  consoleLogs.value = [
      `> 连接到节点任务 [${node.data.label || node.data.prompt}]...`, 
      `> 打包装载代码至物理容器...`, 
      `> ${demoMode ? '🐢 探针慢进演示模式挂载 (Trace Mode = ON)' : '⚡ CPython原生极速模式 (Trace Mode = OFF)'}\n`
  ];
  currentIsError.value = false;
  node.data.output = '';
  
  try {
    const parsedParams: Record<string, any> = {}
    if (node.data.parameters) {
       node.data.parameters.forEach((p: any) => {
           let val = paramValues[p.name]
           if (p.type.toLowerCase() === 'number') {
             val = isNaN(Number(val)) ? val : Number(val)
           }
           parsedParams[p.name] = val
       })
    }

    const payload = {
        code,
        params: parsedParams,
        dependencies: node.data.dependencies || [],
        demo_mode: demoMode,
        project_id: currentProject.value?.id
    }

    const response = await fetch(`${API_BASE}/sandbox/execute_stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    
    if (!response.body) throw new Error('沙箱流媒体握手失败，网络协议不同步');
    
    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = '';
    
    while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        
        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n\n');
        buffer = lines.pop() || '';
        
        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const dataStr = line.substring(6);
                if (dataStr === '[DONE]') break;
                
                try {
                    const data = JSON.parse(dataStr);
                    if (data.type === 'log') {
                        let content = data.content;
                        
                        if (content.includes('[SYSTEM_SYNC_STEP_POINTER]:')) {
                            const match = content.match(/\[SYSTEM_SYNC_STEP_POINTER\]:\s*(\d+)/);
                            if (match) {
                                let stepIdx = Number(match[1]);
                                if (stepIdx >= 0) node.data.activeStep = stepIdx;
                            }
                            continue;
                        }

                        if(content.endsWith('\n')) content = content.substring(0, content.length-1);
                        if (content.trim()) {
                            consoleLogs.value.push(content);
                            node.data.output += data.content;
                        }
                    } else if (data.type === 'error') {
                        currentIsError.value = true;
                        node.data.output += `\n[FATAL ERROR] ${data.content}`;
                        consoleLogs.value.push(`\n[FATAL ERROR] ${data.content}`);
                    }
                    setTimeout(() => {
                        if (consoleBox.value) {
                           consoleBox.value.scrollTop = consoleBox.value.scrollHeight;
                        }
                    }, 50);
                } catch(e) {}
            }
        }
    }
    
    node.data.isError = currentIsError.value;
    if (node.data.isError) {
      ElMessage.error(`沙箱执行异常崩盘！详情见终端输出`);
      setTimeout(() => { openCodeEditor(nodeId, node.data.code); }, 500);
    } else {
      ElMessage.success(`节点安全执行完毕！`);
      if (node.data.steps && node.data.steps.length > 0) {
         node.data.activeStep = node.data.steps.length - 1;
      }
    }

  } catch (error: any) {
    ElMessage.error("沙箱服务引擎失联");
    node.data.isError = true;
    currentIsError.value = true;
    node.data.output = "请求后端网络失败";
    consoleLogs.value.push(`\n网络通信故障: ${error.message}`);
  } finally {
    node.data.running = false;
    isSandboxRunning.value = false;
    setTimeout(() => {
        if (consoleBox.value) {
           consoleBox.value.scrollTop = consoleBox.value.scrollHeight;
        }
    }, 50);
  }
}

const viewOutput = (nodeId: string, output: string, isError: boolean) => {
  consoleLogs.value = output.split('\n');
  currentIsError.value = isError;
  isSandboxRunning.value = false;
  consoleVisible.value = true;
}

const openNodeDir = async (paramValues: any) => {
  if (!paramValues) return;
  const targetDir = paramValues['work_dir'] || paramValues['output_dir'] || paramValues['root_dir'] || paramValues['workspace'] || paramValues['dir'] || paramValues['path'] || '';
  if (!targetDir) {
    ElMessage.warning('💡 此节点的外部参数中找不到名为 work_dir/output_dir/root_dir 等工作目录特征变量，不知道该打开哪个目录 🤷‍♂️');
    return;
  }
  
  try {
    const res = await axios.post(`${API_BASE}/sandbox/open_dir`, { path: String(targetDir).trim() });
    if (res.data.success) {
      ElMessage.success(res.data.message);
    } else {
      ElMessage.warning(res.data.message || '目录打开操作遇到了系统拦截');
    }
  } catch (error: any) {
    ElMessage.error('调用底层操作系统的文件浏览器通道失效:' + (error.message || '网络连接发生故障'));
  }
}

// 串行阻塞执行所有节点
const runAllNodesSequentially = async () => {
    if (nodes.value.length === 0) return;
    
    isProjectRunning.value = true;
    try {
        for (let i = 0; i < nodes.value.length; i++) {
            const node = nodes.value[i];
            
            // 跳过无效节点
            if (!node || !node.data || !node.data.code) continue;

            ElMessage.success(`[${i + 1}/${nodes.value.length}] 系统将开始执行节点: ${node.data.label || '无名节点'}`);
            
            // 等待当前节点执行完毕（runNode 内部已经是 async 的，直到收到[DONE]才会释放协程）
            await runNode(node.id, node.data.code, node.data.paramValues, false);
            
            // 一旦出错（语法错误、沙箱崩溃等），立刻执行阻断短路保护
            if (currentIsError.value || node.data.isError) {
                ElMessage.error(`❌ 在第 ${i + 1} 个节点发生停机错误！已触发故障断路器，强力中止后续节点执行。`);
                break;
            }
        }
        
        if (!currentIsError.value) {
            ElMessage.success(`✅ 流水线顺畅运行结束，当前工程内 ${nodes.value.length} 个串联节点已全部顺序执行完毕！`);
        }
    } catch (e: any) {
        ElMessage.error(`流水线引擎发生整体崩溃: ${e.message}`);
    } finally {
        isProjectRunning.value = false;
    }
}

// ==================== AI 修复功能 ====================

const openAiFixDialog = () => {
  aiFixUserMsg.value = ''
  aiFixPreview.value = ''
  aiFixDialogVisible.value = true
}

const submitAiFix = async () => {
  if (!runningNodeId.value) return
  const node = nodes.value.find(n => n.id === runningNodeId.value)
  if (!node) return

  isAiFixing.value = true
  aiFixPreview.value = ''
  
  // 打开透明监听台
  drawerVisible.value = true

  try {
    const terminalText = consoleLogs.value.join('\n')
    const rawResult = await fetchStream(`${API_BASE}/kimi/fix_stream`, {
      original_code: node.data.code,
      terminal_output: terminalText,
      user_feedback: aiFixUserMsg.value
    })

    // 清理可能的 markdown 包裹
    let fixedCode = rawResult.trim()
    if (fixedCode.startsWith('```python')) fixedCode = fixedCode.substring(9)
    if (fixedCode.startsWith('```')) fixedCode = fixedCode.substring(3)
    if (fixedCode.endsWith('```')) fixedCode = fixedCode.substring(0, fixedCode.length - 3)
    fixedCode = fixedCode.trim()

    // 将修复后的代码写回节点
    node.data.code = fixedCode
    aiFixDialogVisible.value = false
    
    ElMessage.success('🎉 AI 已完成代码修复！代码已自动更新到节点，可直接重新执行。')
    chatLogs.value.push({ role: 'system', content: `🤖 AI 自动修复了节点「${node.data.label || node.data.prompt}」的代码。` })
    
  } catch (error: any) {
    ElMessage.error('AI 修复失败：' + error.message)
  } finally {
    isAiFixing.value = false
  }
}

// ==================== 编辑器内 AI 对话 ====================

const submitEditorAiChat = async () => {
  if (!editorAiMsg.value.trim()) return
  isEditorAiChatting.value = true
  const instruction = editorAiMsg.value
  editorAiMsg.value = ''

  // 打开透明监听台
  drawerVisible.value = true

  try {
    const rawResult = await fetchStream(`${API_BASE}/kimi/code_chat_stream`, {
      current_code: editingCode.value,
      instruction: instruction
    })

    // 清理可能的 markdown 包裹
    let newCode = rawResult.trim()
    if (newCode.startsWith('```python')) newCode = newCode.substring(9)
    if (newCode.startsWith('```')) newCode = newCode.substring(3)
    if (newCode.endsWith('```')) newCode = newCode.substring(0, newCode.length - 3)
    newCode = newCode.trim()

    // 将 AI 返回的代码直接写入编辑器，并自动保存到节点
    editingCode.value = newCode
    const node = nodes.value.find(n => n.id === editingNodeId.value)
    if (node) {
      node.data.code = newCode
    }
    ElMessage.success('✨ AI 已根据您的指令修改了代码并已自动保存生效。')

  } catch (error: any) {
    ElMessage.error('AI 对话失败：' + error.message)
  } finally {
    isEditorAiChatting.value = false
  }
}

// ==================== 初始化 ====================
onMounted(async () => {
  await fetchProjectList()
})
</script>

<style>
/* 清理默认自带白壳影响 */
.vue-flow__node-python {
  border: none !important;
  background: transparent !important;
  padding: 0 !important;
  box-shadow: none !important;
}

/* 彻底解决非模态弹窗的透明遮罩层吞噬鼠标点击的问题 */
.el-overlay {
  pointer-events: none !important;
}
.el-overlay .el-dialog,
.el-overlay .el-message-box,
.el-overlay .el-drawer {
  pointer-events: auto !important;
}

/* 侧边面板滑入/滑出动画 */
.slide-panel-enter-active,
.slide-panel-leave-active {
  transition: transform 0.3s ease;
}
.slide-panel-enter-from,
.slide-panel-leave-to {
  transform: translateX(100%);
}

/* 多行文本截断 */
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
